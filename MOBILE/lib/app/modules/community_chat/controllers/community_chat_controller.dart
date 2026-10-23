import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/ws_client.dart';
import '../../../data/models/api/game.dart' show stickerAsset;
import '../../../data/models/api/social.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../models/community_chat_models.dart';

/// Realtime group chat over WebSocket (`/ws/groups/<id>/`), REST for history and as a fallback.
class CommunityChatController extends GetxController {
  final RxList<CommunityChatMessage> messages = <CommunityChatMessage>[].obs;
  late final CommunityGroupDetails groupDetails;
  final ScrollController scrollController = ScrollController();
  final RxBool connected = false.obs;

  late final int _groupId;
  WsClient? _ws;
  StreamSubscription? _sub;
  final Set<int> _leaderIds = {};
  final Set<String> _seen = {};
  int _clientSeq = 0;

  @override
  void onInit() {
    super.onInit();
    groupDetails = Get.arguments as CommunityGroupDetails;
    _groupId = int.tryParse(groupDetails.group.groupId) ?? 0;
    if (int.tryParse(groupDetails.group.leaderId) != null) _leaderIds.add(int.parse(groupDetails.group.leaderId));
    _load();
  }

  Future<void> _load() async {
    try {
      final members = await CommunityRepository.members(_groupId);
      _leaderIds.addAll(members.where((m) => m.role == 'leader').map((m) => m.user.id));
    } catch (_) {}
    try {
      final (history, _) = await ChatRepository.groupMessages(_groupId);
      messages.assignAll(history.map(_map));
      _seen.addAll(history.map((m) => 'id:${m.id}'));
      _scrollToBottom();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
    _ws = WsClient('/ws/groups/$_groupId/')..connect();
    _ws!.connected.addListener(() => connected.value = _ws!.connected.value);
    _sub = _ws!.events.listen((e) {
      if (e.event == 'message') {
        _add(ChatMessage.fromJson(e.payload));
      } else if (e.event == 'error') {
        Get.snackbar('Không gửi được', '${e.payload['detail']}', snackPosition: SnackPosition.BOTTOM);
      }
    });
  }

  CommunityChatMessage _map(ChatMessage m) {
    final isSticker = m.kind == 'sticker';
    final content = switch (m.kind) {
      'sticker' => stickerAsset(m.sticker),
      'badge' => '🏅 ${m.badgeName ?? 'Huy hiệu'}',
      _ => m.content,
    };
    return CommunityChatMessage(
      senderName: m.displayName,
      content: content,
      isCurrentUser: m.userId == AuthService.to.userId,
      isLeader: _leaderIds.contains(m.userId),
      isSticker: isSticker,
      timestamp: m.createdAt,
      messageId: '${m.id}',
    );
  }

  void _add(ChatMessage m) {
    if (!_seen.add('id:${m.id}')) return;
    // replace the optimistic copy sent by this device
    if (m.clientId.isNotEmpty) {
      final i = messages.indexWhere((x) => x.messageId == 'tmp:${m.clientId}');
      if (i >= 0) {
        messages[i] = _map(m);
        return;
      }
    }
    messages.add(_map(m));
    _scrollToBottom();
  }

  Future<void> sendMessage(String text, {String kind = 'text', String sticker = ''}) async {
    final content = text.trim();
    if (kind == 'text' && content.isEmpty) return;
    final clientId = '${AuthService.to.userId}-${DateTime.now().millisecondsSinceEpoch}-${_clientSeq++}';
    messages.add(CommunityChatMessage(
      senderName: AuthService.to.currentUser?.displayName ?? '',
      content: kind == 'sticker' ? stickerAsset(sticker) : content,
      isCurrentUser: true,
      isLeader: _leaderIds.contains(AuthService.to.userId),
      isSticker: kind == 'sticker',
      timestamp: DateTime.now(),
      messageId: 'tmp:$clientId',
    ));
    _scrollToBottom();
    final sent = _ws?.send({'action': 'send', 'kind': kind, 'content': content, 'sticker': sticker, 'client_id': clientId}) ?? false;
    if (!sent) {
      try {
        _add(await ChatRepository.sendGroup(_groupId, kind: kind, content: content, sticker: sticker, clientId: clientId));
      } catch (e) {
        messages.removeWhere((m) => m.messageId == 'tmp:$clientId');
        Get.snackbar('Không gửi được', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
      }
    }
  }

  Future<void> sendSticker(String code) => sendMessage('', kind: 'sticker', sticker: code);

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (scrollController.hasClients) {
        scrollController.animateTo(scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  @override
  void onClose() {
    _sub?.cancel();
    _ws?.dispose();
    scrollController.dispose();
    super.onClose();
  }
}
