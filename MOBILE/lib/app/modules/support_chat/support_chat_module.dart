import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../../core/network/ws_client.dart';
import '../../core/theme/app_colors.dart';
import '../../data/models/api/social.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/auth_service.dart';

/// Chat between a learner and the teachers / support staff (`/ws/support/<id>/`).
class SupportChatController extends GetxController {
  final RxList<ChatMessage> messages = <ChatMessage>[].obs;
  final RxBool loading = true.obs;
  final RxBool staffTyping = false.obs;
  final input = TextEditingController();
  final scroll = ScrollController();
  SupportConversation? conversation;
  WsClient? _ws;
  StreamSubscription? _sub;
  Timer? _typingReset;

  @override
  void onInit() {
    super.onInit();
    _open();
  }

  Future<void> _open() async {
    try {
      conversation = await ChatRepository.openSupport();
      messages.assignAll(await ChatRepository.supportMessages(conversation!.id));
      _ws = WsClient('/ws/support/${conversation!.id}/')..connect();
      _sub = _ws!.events.listen((e) {
        if (e.event == 'message') {
          final m = ChatMessage.fromJson(e.payload);
          final i = messages.indexWhere((x) => x.pending && x.clientId == m.clientId && m.clientId.isNotEmpty);
          if (i >= 0) {
            messages[i] = m;
          } else if (!messages.any((x) => x.id == m.id)) {
            messages.add(m);
          }
          if (m.userId != AuthService.to.userId) _ws!.send({'action': 'read'});
          _toBottom();
        } else if (e.event == 'typing' && e.payload['user'] != AuthService.to.userId) {
          staffTyping.value = true;
          _typingReset?.cancel();
          _typingReset = Timer(const Duration(seconds: 3), () => staffTyping.value = false);
        }
      });
      _toBottom();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      loading.value = false;
    }
  }

  Future<void> send() async {
    final text = input.text.trim();
    if (text.isEmpty || conversation == null) return;
    input.clear();
    final clientId = '${AuthService.to.userId}-${DateTime.now().millisecondsSinceEpoch}';
    messages.add(ChatMessage(id: 0, userId: AuthService.to.userId, displayName: AuthService.to.currentUser?.displayName ?? '',
        content: text, clientId: clientId, createdAt: DateTime.now(), pending: true));
    _toBottom();
    if (_ws?.send({'action': 'send', 'content': text, 'client_id': clientId}) != true) {
      try {
        final m = await ChatRepository.sendSupport(conversation!.id, text, clientId: clientId);
        final i = messages.indexWhere((x) => x.clientId == clientId);
        if (i >= 0) messages[i] = m;
      } catch (e) {
        messages.removeWhere((x) => x.clientId == clientId && x.pending);
        Get.snackbar('Không gửi được', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
      }
    }
  }

  void typing() => _ws?.send({'action': 'typing'});

  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (scroll.hasClients) scroll.jumpTo(scroll.position.maxScrollExtent);
      });

  @override
  void onClose() {
    _typingReset?.cancel();
    _sub?.cancel();
    _ws?.dispose();
    input.dispose();
    scroll.dispose();
    super.onClose();
  }
}

class SupportChatView extends GetView<SupportChatController> {
  const SupportChatView({super.key});

  @override
  Widget build(BuildContext context) {
    final me = AuthService.to.userId;
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(title: const Text('Hỏi giáo viên'), backgroundColor: AppColors.appBarBackground),
      body: Column(children: [
        Expanded(
          child: Obx(() {
            if (controller.loading.value) return const Center(child: CircularProgressIndicator());
            if (controller.messages.isEmpty) {
              return Center(
                child: Padding(
                  padding: EdgeInsets.all(24.w),
                  child: const Text('Bạn có thắc mắc về từ vựng, phát âm hay bài kiểm tra? Hãy nhắn cho giáo viên nhé!',
                      textAlign: TextAlign.center),
                ),
              );
            }
            return ListView.builder(
              controller: controller.scroll,
              padding: EdgeInsets.all(12.w),
              itemCount: controller.messages.length,
              itemBuilder: (_, i) {
                final m = controller.messages[i];
                final mine = m.userId == me;
                return Align(
                  alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: EdgeInsets.symmetric(vertical: 4.h),
                    padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
                    constraints: BoxConstraints(maxWidth: 0.75.sw),
                    decoration: BoxDecoration(
                      color: mine ? AppColors.buttonActive : Colors.white,
                      borderRadius: BorderRadius.circular(14.r),
                    ),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      if (!mine) Text(m.displayName, style: TextStyle(fontSize: 11.sp, fontWeight: FontWeight.w700, color: AppColors.textSecondary)),
                      Text(m.content, style: TextStyle(color: mine ? Colors.white : AppColors.textPrimary, fontSize: 15.sp)),
                      if (m.pending) Text('Đang gửi…', style: TextStyle(fontSize: 10.sp, color: Colors.white70)),
                    ]),
                  ),
                );
              },
            );
          }),
        ),
        Obx(() => controller.staffTyping.value
            ? Padding(padding: EdgeInsets.only(left: 16.w, bottom: 4.h), child: const Align(alignment: Alignment.centerLeft, child: Text('Giáo viên đang nhập…')))
            : const SizedBox()),
        SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(12.w, 0, 12.w, 8.h),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: controller.input,
                  onChanged: (_) => controller.typing(),
                  onSubmitted: (_) => controller.send(),
                  decoration: InputDecoration(
                    hintText: 'Nhập tin nhắn…',
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(24.r), borderSide: BorderSide.none),
                  ),
                ),
              ),
              IconButton(icon: const Icon(Icons.send_rounded, color: AppColors.buttonActive), onPressed: controller.send),
            ]),
          ),
        ),
      ]),
    );
  }
}
