import 'package:flutter/foundation.dart';
import 'package:get_storage/get_storage.dart';

import '../../core/network/api_client.dart';
import '../models/api/common.dart';
import '../models/api/learning_extra.dart';
import '../repositories/repositories.dart';

/// Photo detection without network: the phone's TFLite model finds the objects, the word cards come from a copy of
/// `/detections/labels/` kept on the phone, and what the learner saves / reports is queued and sent (log + confirm)
/// the next time the server answers.
class OfflineDetections {
  OfflineDetections._();

  static final GetStorage _box = GetStorage();
  static const _labelsKey = 'detect.labels';
  static const _labelsAtKey = 'detect.labels_at';
  static const _pendingKey = 'detect.pending';
  static const _refreshEvery = Duration(minutes: 10);
  static bool _flushing = false;

  /// Keep the word cards of every detectable object (called after each detection that reached the server).
  static Future<void> refreshLabels({bool force = false}) async {
    final at = DateTime.tryParse(_box.read<String>(_labelsAtKey) ?? '');
    if (!force && at != null && DateTime.now().difference(at) < _refreshEvery) return;
    try {
      final raw = await DetectionRepository.labelsRaw();
      await _box.write(_labelsKey, raw);
      await _box.write(_labelsAtKey, DateTime.now().toIso8601String());
    } catch (e) {
      if (kDebugMode) debugPrint('[OfflineDetections] labels not refreshed: $e');
    }
  }

  static Map<String, Map<String, dynamic>> get _cards {
    final raw = _box.read(_labelsKey);
    if (raw is! List) return {};
    return {
      for (final r in raw.whereType<Map>())
        asString(r['label']): Map<String, dynamic>.from(asMap(r['card'])),
    };
  }

  static bool get hasLabels => _cards.isNotEmpty;

  static List<DetectionAlternative> cachedLabels() =>
      _cards.entries.map((e) => DetectionAlternative.fromJson({'label': e.key, 'confidence': 0, 'card': e.value})).toList();

  /// A result built on the phone: id 0, items numbered by their position in [items] (the TFLite boxes).
  static DetectionResult result(String model, int ms, List<Map<String, dynamic>> items) {
    final cards = _cards;
    return DetectionResult(
      id: 0,
      model: model,
      device: 'on_device',
      inferenceMs: ms,
      items: [
        for (var i = 0; i < items.length; i++)
          DetectedItem.fromJson({
            ...items[i],
            'id': i,
            'card': cards[items[i]['label']],
            'alternatives': [
              for (final t in (items[i]['top_k'] as List? ?? const []).whereType<Map>())
                if (t['label'] != items[i]['label'] && cards[t['label']] != null)
                  {'label': t['label'], 'confidence': t['confidence'], 'card': cards[t['label']]},
            ],
            'uncertain': asDouble(items[i]['confidence']) < 0.6 && (items[i]['top_k'] as List? ?? const []).length > 1,
          }),
      ],
    );
  }

  static List<Map<String, dynamic>> get _pending =>
      (_box.read(_pendingKey) as List? ?? const []).whereType<Map>().map((m) => Map<String, dynamic>.from(m)).toList();

  static int get pendingCount => _pending.length;

  /// Queue an offline result with the learner's choices (selected words, error reports).
  static Future<void> queue(DetectionResult r, List<Map<String, dynamic>> items, {int? topic}) async {
    final list = _pending
      ..add({
        'model': r.model,
        'ms': r.inferenceMs ?? 0,
        'items': items,
        'topic': topic,
        'choices': [
          for (final it in r.items)
            {
              'index': it.id,
              'selected': it.selected,
              'feedback': it.feedback,
              'corrected_label': it.picked ?? '',
              'not_object': it.notObject,
            },
        ],
        'at': DateTime.now().toIso8601String(),
      });
    await _box.write(_pendingKey, list);
  }

  /// Send the queued results; returns how many were synced. Stops at the first network error (still offline).
  static Future<int> flush() async {
    if (_flushing) return 0;
    _flushing = true;
    var done = 0;
    try {
      while (true) {
        final list = _pending;
        if (list.isEmpty) break;
        final p = list.first;
        try {
          if (p['detection_id'] == null) {
            final items = asMapList(p['items']);
            final logged = await DetectionRepository.logOnDevice(asString(p['model']), asInt(p['ms']), items);
            // remember the server ids: if the network drops before confirm, the retry does not log it twice
            p['detection_id'] = logged.id;
            p['confirm'] = [
              for (final c in asMapList(p['choices']))
                if (_match(logged, items, asInt(c['index'])) case final id?) {...c, 'id': id}..remove('index'),
            ];
            await _box.write(_pendingKey, list);
          }
          final choices = asMapList(p['confirm']);
          if (choices.isNotEmpty) {
            final topic = p['topic'];
            await DetectionRepository.confirmRaw(asInt(p['detection_id']), choices, topic: topic is int ? topic : null);
          }
        } on ApiException catch (e) {
          if (e.isNetwork || e.statusCode == 401 || (e.statusCode ?? 0) >= 500) break; // try again later
          if (kDebugMode) debugPrint('[OfflineDetections] dropped a queued result: ${e.message}');
        }
        await _box.write(_pendingKey, list.sublist(1));
        done++;
      }
    } finally {
      _flushing = false;
    }
    return done;
  }

  /// Server item stored for the [index]-th phone box (same label, same box).
  static int? _match(DetectionResult logged, List<Map<String, dynamic>> items, int index) {
    if (index < 0 || index >= items.length) return null;
    final want = items[index];
    final bbox = (want['bbox'] as List? ?? const []).map(asDouble).toList();
    for (final it in logged.items) {
      if (it.label != want['label'] || it.bbox.length != bbox.length) continue;
      var same = true;
      for (var k = 0; k < bbox.length; k++) {
        if ((it.bbox[k] - bbox[k]).abs() > 1e-3) same = false;
      }
      if (same) return it.id;
    }
    return null;
  }
}
