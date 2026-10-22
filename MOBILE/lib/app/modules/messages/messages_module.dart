import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../../core/network/ws_client.dart';
import '../../core/theme/app_colors.dart';
import '../../data/models/api/common.dart';
import '../../data/services/auth_service.dart';
import '../../data/services/realtime_service.dart';
import '../../routes/app_pages.dart';
import '../community/views/report_user_sheet.dart';

/// Private messages between two learners who follow each other (server: apps.chat, /messages/threads/).
/// Children's accounts never see this. New messages arrive on the user's /ws/events/ socket (RealtimeService).

class DirectMessage {
  DirectMessage({required this.id, required this.sender, required this.content, this.clientId = '', this.readAt,
      required this.createdAt, this.pending = false});

  final int id;
  final int sender;
  final String content;
  final String clientId;
  final DateTime? readAt;
  final DateTime createdAt;
  final bool pending;

  factory DirectMessage.fromJson(Map<String, dynamic> j) => DirectMessage(
        id: asInt(j['id']),
        sender: asInt(j['sender']),
        content: asString(j['content']),
        clientId: asString(j['client_id']),
        readAt: DateTime.tryParse(asString(j['read_at'])),
        createdAt: DateTime.tryParse(asString(j['created_at']))?.toLocal() ?? DateTime.now(),
      );

  DirectMessage seen() => DirectMessage(id: id, sender: sender, content: content, clientId: clientId,
      readAt: readAt ?? DateTime.now(), createdAt: createdAt);
}

class DirectThread {
  DirectThread({required this.id, required this.other, this.unread = 0, this.canMessage = true, this.last});

  final int id;
  final Author other;
  final int unread;
  final bool canMessage;
  final DirectMessage? last;

  factory DirectThread.fromJson(Map<String, dynamic> j) => DirectThread(
        id: asInt(j['id']),
        other: Author.fromJson(asMap(j['other'])),
        unread: asInt(j['unread']),
        canMessage: j['can_message'] == true,
        last: j['last_message'] is Map ? DirectMessage.fromJson(asMap(j['last_message'])) : null,
      );
}

class MessagesRepository {
  static ApiClient get _api => ApiClient.to;

  static Future<List<DirectThread>> threads() async =>
      asMapList(await _api.get('/messages/threads/')).map(DirectThread.fromJson).toList();
  static Future<DirectThread> thread(int id) async => DirectThread.fromJson(asMap(await _api.get('/messages/threads/$id/')));
  static Future<DirectThread> open(int userId) async =>
      DirectThread.fromJson(asMap(await _api.post('/messages/threads/', data: {'user': userId})));
  static Future<(List<DirectMessage>, bool)> messages(int id, {int? before}) async {
    final d = asMap(await _api.get('/messages/threads/$id/messages/', query: {'before': before}));
    return (asMapList(d['results']).map(DirectMessage.fromJson).toList(), d['has_more'] == true);
  }

  static Future<DirectMessage> send(int id, String content, String clientId) async => DirectMessage.fromJson(
      asMap(await _api.post('/messages/threads/$id/messages/', data: {'content': content, 'client_id': clientId})));
  static Future<void> read(int id) => _api.post('/messages/threads/$id/read/');

  /// "Nhắn tin" on a profile: open (or create) the conversation and go there.
  static Future<void> openWith(int userId) async {
    try {
      final t = await open(userId);
      Get.toNamed(Routes.directChat, arguments: t.id);
    } catch (e) {
      Get.snackbar('Không nhắn tin được', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }
}

/// Avatars are either a bundled brand picture (assets/…) or an uploaded photo (http…).
ImageProvider avatarImage(String path) =>
    path.startsWith('http') ? NetworkImage(path) as ImageProvider : AssetImage(path);

String _when(DateTime t) {
  final now = DateTime.now();
  String two(int n) => n.toString().padLeft(2, '0');
  return t.year == now.year && t.month == now.month && t.day == now.day
      ? '${two(t.hour)}:${two(t.minute)}'
      : '${two(t.day)}/${two(t.month)}';
}

// ---------------------------------------------------------------- list of conversations

class MessagesController extends GetxController {
  final RxList<DirectThread> threads = <DirectThread>[].obs;
  final RxBool loading = true.obs;
  StreamSubscription? _sub;

  @override
  void onInit() {
    super.onInit();
    load();
    _sub = RealtimeService.to.directMessages.listen((_) => load());
  }

  Future<void> load() async {
    try {
      threads.assignAll(await MessagesRepository.threads());
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      loading.value = false;
    }
  }

  @override
  void onClose() {
    _sub?.cancel();
    super.onClose();
  }
}

class MessagesView extends GetView<MessagesController> {
  const MessagesView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(title: const Text('Tin nhắn'), backgroundColor: AppColors.appBarBackground),
      body: Obx(() {
        if (controller.loading.value) return const Center(child: CircularProgressIndicator());
        if (controller.threads.isEmpty) {
          return Center(
            child: Padding(
              padding: EdgeInsets.all(32.w),
              child: Text('Hai bạn theo dõi nhau là nhắn tin được. Mở trang cá nhân của một bạn học và bấm “Nhắn tin”.',
                  textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary, fontSize: 15.sp)),
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: controller.load,
          child: ListView.separated(
            padding: EdgeInsets.symmetric(vertical: 8.h),
            itemCount: controller.threads.length,
            separatorBuilder: (_, __) => Divider(height: 1, color: AppColors.line),
            itemBuilder: (_, i) {
              final t = controller.threads[i];
              final bold = t.unread > 0;
              return ListTile(
                onTap: () async {
                  await Get.toNamed(Routes.directChat, arguments: t.id);
                  controller.load();
                },
                leading: CircleAvatar(backgroundImage: avatarImage(t.other.avatarOrDefault)),
                title: Row(children: [
                  Expanded(child: Text(t.other.displayName, overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontWeight: bold ? FontWeight.w800 : FontWeight.w600, color: AppColors.textPrimary))),
                  if (t.last != null)
                    Text(_when(t.last!.createdAt), style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
                ]),
                subtitle: Row(children: [
                  Expanded(child: Text(t.last?.content ?? '', maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: bold ? AppColors.textPrimary : AppColors.textSecondary))),
                  if (bold)
                    Container(
                      margin: EdgeInsets.only(left: 8.w),
                      padding: EdgeInsets.symmetric(horizontal: 7.w, vertical: 1.h),
                      decoration: BoxDecoration(color: AppColors.buttonActive, borderRadius: BorderRadius.circular(10.r)),
                      child: Text('${t.unread}', style: TextStyle(color: Colors.white, fontSize: 11.sp, fontWeight: FontWeight.w800)),
                    ),
                ]),
              );
            },
          ),
        );
      }),
    );
  }
}

// ---------------------------------------------------------------- one conversation

class DirectChatController extends GetxController {
  late final int threadId;
  final Rxn<DirectThread> thread = Rxn<DirectThread>();
  final RxList<DirectMessage> messages = <DirectMessage>[].obs;
  final RxBool loading = true.obs;
  final RxBool hasMore = false.obs;
  final input = TextEditingController();
  final scroll = ScrollController();
  StreamSubscription? _sub;

  int get me => AuthService.to.userId;

  @override
  void onInit() {
    super.onInit();
    threadId = Get.arguments as int;
    _sub = RealtimeService.to.directMessages.listen(_onEvent);
    _load();
  }

  Future<void> _load() async {
    try {
      thread.value = await MessagesRepository.thread(threadId);
      final (list, more) = await MessagesRepository.messages(threadId);
      messages.assignAll(list);
      hasMore.value = more;
      _toBottom();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      loading.value = false;
    }
  }

  Future<void> reload() async => thread.value = await MessagesRepository.thread(threadId);

  Future<void> older() async {
    if (messages.isEmpty) return;
    final (list, more) = await MessagesRepository.messages(threadId, before: messages.first.id);
    messages.insertAll(0, list);
    hasMore.value = more;
  }

  void _onEvent(WsEvent e) {
    if (asInt(e.payload['thread']) != threadId) return;
    if (e.event == 'dm_read') {
      messages.assignAll(messages.map((m) => m.sender == me && m.readAt == null ? m.seen() : m));
      return;
    }
    final m = DirectMessage.fromJson(e.payload);
    final i = messages.indexWhere((x) => x.clientId.isNotEmpty && x.clientId == m.clientId);
    if (i >= 0) {
      messages[i] = m;
    } else if (!messages.any((x) => x.id == m.id)) {
      messages.add(m);
      _toBottom();
    }
    if (m.sender != me) MessagesRepository.read(threadId).catchError((_) {});
  }

  Future<void> send() async {
    final text = input.text.trim();
    if (text.isEmpty) return;
    input.clear();
    final clientId = '$me-${DateTime.now().millisecondsSinceEpoch}';
    messages.add(DirectMessage(id: 0, sender: me, content: text, clientId: clientId, createdAt: DateTime.now(), pending: true));
    _toBottom();
    try {
      final m = await MessagesRepository.send(threadId, text, clientId);
      final i = messages.indexWhere((x) => x.clientId == clientId);
      if (i >= 0) messages[i] = m;
    } catch (e) {
      messages.removeWhere((x) => x.clientId == clientId && x.pending);
      input.text = text;
      Get.snackbar('Không gửi được', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (scroll.hasClients) scroll.jumpTo(scroll.position.maxScrollExtent);
      });

  @override
  void onClose() {
    _sub?.cancel();
    input.dispose();
    scroll.dispose();
    super.onClose();
  }
}

class DirectChatView extends GetView<DirectChatController> {
  const DirectChatView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.appBarBackground,
        title: Obx(() {
          final t = controller.thread.value;
          if (t == null) return const Text('Tin nhắn');
          return Row(children: [
            CircleAvatar(radius: 16.r, backgroundImage: avatarImage(t.other.avatarOrDefault)),
            SizedBox(width: 10.w),
            Expanded(child: Text(t.other.displayName, overflow: TextOverflow.ellipsis)),
          ]);
        }),
        actions: [
          Obx(() {
            final t = controller.thread.value;
            if (t == null) return const SizedBox();
            return IconButton(
              tooltip: 'Báo cáo',
              icon: const Icon(Icons.flag_outlined),
              onPressed: () async {
                if (await showReportUserSheet(userId: t.other.id, name: t.other.displayName, threadId: t.id)) {
                  controller.reload();
                }
              },
            );
          }),
        ],
      ),
      body: Column(children: [
        Expanded(
          child: Obx(() {
            if (controller.loading.value) return const Center(child: CircularProgressIndicator());
            final list = controller.messages;
            if (list.isEmpty) {
              return Center(
                child: Padding(
                  padding: EdgeInsets.all(24.w),
                  child: Text('Gửi lời chào đầu tiên. Thử viết một câu bằng ngôn ngữ hai bạn đang học!',
                      textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
                ),
              );
            }
            final lastMine = list.lastIndexWhere((m) => m.sender == controller.me);
            return ListView.builder(
              controller: controller.scroll,
              padding: EdgeInsets.all(12.w),
              itemCount: list.length + (controller.hasMore.value ? 1 : 0),
              itemBuilder: (_, index) {
                if (controller.hasMore.value && index == 0) {
                  return Center(child: TextButton(onPressed: controller.older, child: const Text('Tin cũ hơn')));
                }
                final i = index - (controller.hasMore.value ? 1 : 0);
                final m = list[i];
                final mine = m.sender == controller.me;
                return Column(
                  crossAxisAlignment: mine ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                  children: [
                    Container(
                      margin: EdgeInsets.only(top: 6.h),
                      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
                      constraints: BoxConstraints(maxWidth: 0.75.sw),
                      decoration: BoxDecoration(
                        color: mine ? AppColors.buttonActive : AppColors.surface,
                        borderRadius: BorderRadius.circular(16.r),
                      ),
                      child: Text(m.content, style: TextStyle(color: mine ? Colors.white : AppColors.textPrimary, fontSize: 15.sp)),
                    ),
                    if (i == lastMine)
                      Padding(
                        padding: EdgeInsets.only(top: 2.h),
                        child: Text(m.pending ? 'Đang gửi…' : m.readAt != null ? 'Đã xem' : 'Đã gửi',
                            style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary)),
                      ),
                  ],
                );
              },
            );
          }),
        ),
        Obx(() {
          final t = controller.thread.value;
          if (t != null && !t.canMessage) {
            return SafeArea(
              child: Padding(
                padding: EdgeInsets.all(12.w),
                child: Text('Hai bạn không còn theo dõi nhau nên không gửi thêm tin được.',
                    textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
              ),
            );
          }
          return SafeArea(
            child: Padding(
              padding: EdgeInsets.fromLTRB(12.w, 4.h, 12.w, 8.h),
              child: Row(children: [
                Expanded(
                  child: TextField(
                    controller: controller.input,
                    maxLength: 1000,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => controller.send(),
                    decoration: InputDecoration(
                      hintText: 'Nhập tin nhắn…',
                      counterText: '',
                      filled: true,
                      fillColor: AppColors.surface,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24.r), borderSide: BorderSide.none),
                    ),
                  ),
                ),
                IconButton(
                    tooltip: 'Gửi', icon: Icon(Icons.send_rounded, color: AppColors.buttonActive), onPressed: controller.send),
              ]),
            ),
          );
        }),
      ]),
    );
  }
}
