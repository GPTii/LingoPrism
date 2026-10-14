import 'dart:io';
import 'dart:math';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

class OnDeviceBox {
  OnDeviceBox(this.label, this.confidence, this.bbox, this.topK);

  final String label;
  final double confidence;
  final List<double> bbox; // normalized x1, y1, x2, y2
  final List<Map<String, dynamic>> topK;

  Map<String, dynamic> toJson() => {'label': label, 'confidence': confidence, 'bbox': bbox, 'top_k': topK};
}

/// Offline YOLO detection with TFLite (model exported by AI/scripts/train_eval_export.py).
///
/// Supports YOLOv10 NMS-free output `[1, 300, 6]` (x1, y1, x2, y2, score, class) and
/// YOLOv8/11 output `[1, 4 + nc, N]` (cx, cy, w, h, scores…) with NMS.
class OnDeviceDetector {
  OnDeviceDetector._();
  static final OnDeviceDetector instance = OnDeviceDetector._();

  static const modelAsset = 'assets/ml_models/lingoprism_yolov10n.tflite';
  static const labelsAsset = 'assets/ml_models/labels.txt';
  static const double confThreshold = 0.30;
  static const double iouThreshold = 0.45;

  Interpreter? _interpreter;
  List<String> _labels = const [];
  int _size = 640;
  bool _triedLoading = false;

  String get modelName => 'yolov10n-tflite';

  Future<bool> get available async {
    await _ensureLoaded();
    return _interpreter != null;
  }

  Future<void> _ensureLoaded() async {
    if (_interpreter != null || _triedLoading) return;
    _triedLoading = true;
    try {
      final raw = await rootBundle.loadString(labelsAsset);
      _labels = raw.split('\n').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
      final model = await rootBundle.load(modelAsset);
      _interpreter = Interpreter.fromBuffer(model.buffer.asUint8List(), options: InterpreterOptions()..threads = 4);
      _size = _interpreter!.getInputTensor(0).shape[1];
    } catch (e) {
      if (kDebugMode) debugPrint('[OnDeviceDetector] model not available: $e');
      _interpreter = null;
    }
  }

  /// Returns (boxes, inference milliseconds). Throws if no model is bundled.
  Future<(List<OnDeviceBox>, int)> detect(File file) async {
    await _ensureLoaded();
    final interpreter = _interpreter;
    if (interpreter == null) throw StateError('Chưa có mô hình nhận diện trên máy');

    final decoded = img.decodeImage(await file.readAsBytes());
    if (decoded == null) throw StateError('Không thể đọc ảnh');
    final image = img.bakeOrientation(decoded);
    final w = image.width, h = image.height;
    final scale = min(_size / w, _size / h);
    final nw = (w * scale).round(), nh = (h * scale).round();
    final padX = (_size - nw) ~/ 2, padY = (_size - nh) ~/ 2;
    final resized = img.copyResize(image, width: nw, height: nh, interpolation: img.Interpolation.linear);
    final canvas = img.Image(width: _size, height: _size)..clear(img.ColorRgb8(114, 114, 114));
    img.compositeImage(canvas, resized, dstX: padX, dstY: padY);

    final input = Float32List(_size * _size * 3);
    var i = 0;
    for (var y = 0; y < _size; y++) {
      for (var x = 0; x < _size; x++) {
        final p = canvas.getPixel(x, y);
        input[i++] = p.r / 255.0;
        input[i++] = p.g / 255.0;
        input[i++] = p.b / 255.0;
      }
    }

    final outShape = interpreter.getOutputTensor(0).shape;
    final outLen = outShape.reduce((a, b) => a * b);
    final output = Float32List(outLen);
    final sw = Stopwatch()..start();
    interpreter.run(input.buffer.asFloat32List().reshape([1, _size, _size, 3]), output.buffer.asFloat32List().reshape(outShape));
    sw.stop();

    // Map a box from model-input space back to normalized original-image coordinates.
    List<double> toNorm(double x1, double y1, double x2, double y2, bool normalized) {
      final k = normalized ? _size.toDouble() : 1.0;
      double nx(double v) => ((v * k - padX) / scale / w).clamp(0.0, 1.0);
      double ny(double v) => ((v * k - padY) / scale / h).clamp(0.0, 1.0);
      return [nx(x1), ny(y1), nx(x2), ny(y2)];
    }

    final boxes = <OnDeviceBox>[];
    if (outShape.length == 3 && outShape[2] == 6) {
      final n = outShape[1];
      var maxCoord = 0.0;
      for (var r = 0; r < n; r++) {
        maxCoord = max(maxCoord, output[r * 6 + 2]);
      }
      final normalized = maxCoord <= 1.5;
      for (var r = 0; r < n; r++) {
        final o = r * 6;
        final score = output[o + 4];
        if (score < confThreshold) continue;
        final cls = output[o + 5].round();
        if (cls < 0 || cls >= _labels.length) continue;
        final label = _labels[cls];
        boxes.add(OnDeviceBox(label, score, toNorm(output[o], output[o + 1], output[o + 2], output[o + 3], normalized),
            [{'label': label, 'confidence': double.parse(score.toStringAsFixed(4))}]));
      }
    } else {
      // [1, 4 + nc, N]
      final channels = outShape[1], n = outShape[2];
      final nc = channels - 4;
      double at(int c, int j) => output[c * n + j];
      var maxCoord = 0.0;
      for (var j = 0; j < min(n, 200); j++) {
        maxCoord = max(maxCoord, at(2, j));
      }
      final normalized = maxCoord <= 1.5;
      final candidates = <OnDeviceBox>[];
      for (var j = 0; j < n; j++) {
        var best = 0.0, bestC = 0;
        for (var c = 0; c < nc; c++) {
          final s = at(4 + c, j);
          if (s > best) {
            best = s;
            bestC = c;
          }
        }
        if (best < confThreshold || bestC >= _labels.length) continue;
        final cx = at(0, j), cy = at(1, j), bw = at(2, j), bh = at(3, j);
        final scores = List.generate(nc, (c) => MapEntry(c, at(4 + c, j)))..sort((a, b) => b.value.compareTo(a.value));
        candidates.add(OnDeviceBox(_labels[bestC], best, toNorm(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, normalized), [
          for (final e in scores.take(3))
            if (e.key < _labels.length) {'label': _labels[e.key], 'confidence': double.parse(e.value.toStringAsFixed(4))}
        ]));
      }
      boxes.addAll(_nms(candidates));
    }
    boxes.sort((a, b) => b.confidence.compareTo(a.confidence));
    return (boxes, sw.elapsedMilliseconds);
  }

  List<OnDeviceBox> _nms(List<OnDeviceBox> boxes) {
    boxes.sort((a, b) => b.confidence.compareTo(a.confidence));
    final kept = <OnDeviceBox>[];
    for (final b in boxes) {
      final overlaps = kept.any((k) => k.label == b.label && _iou(k.bbox, b.bbox) > iouThreshold);
      if (!overlaps) kept.add(b);
    }
    return kept;
  }

  double _iou(List<double> a, List<double> b) {
    final ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]));
    final iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]));
    final inter = ix * iy;
    final union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter;
    return union <= 0 ? 0 : inter / union;
  }
}
