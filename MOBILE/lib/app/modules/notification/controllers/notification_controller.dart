import 'package:get/get.dart';

import '../../../core/navigation/deep_link.dart';
import '../../../core/network/api_client.dart';
import '../../../data/models/api/common.dart';
import '../../../data/models/api/game.dart';
import '../../../data/models/notification_item.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/realtime_service.dart';

class NotificationController extends GetxController {
  final RxList<NotificationItem> notifications = <NotificationItem>[].obs;
  final RxBool isLoading = false.obs;
  final RxString error = ''.obs;
  final Map<String, AppNotification> _raw = {};

  /// friend / group requests answered right here: notification id → pending · accepted · gone
  final RxMap<String, String> actionStates = <String, String>{}.obs;
  final RxSet<String> answering = <String>{}.obs;

  /// friend_request | group_request, when the notification can be answered from the list
  String? actionOf(String id) => _raw[id]?.action;

  @override
  void onInit() {
    super.onInit();
    loadNotifications();
    RealtimeService.to.notifications.listen((_) => loadNotifications(silent: true));
  }

  static NotificationType _type(String kind) => switch (kind) {
        'follow' || 'friend_request' || 'friend_accept' => NotificationType.follow,
        'like' => NotificationType.postReaction,
        'comment' => NotificationType.postComment,
        'reminder' => NotificationType.streak,
        'league' => NotificationType.rankUp,
        _ => NotificationType.achievement,
      };

  static String _defaultImage(String kind) => switch (kind) {
        'xp_milestone' => 'assets/brand/icons/xp.png',
        'league' => 'assets/brand/rank/rank_5.png',
        'reminder' => 'assets/brand/icons/streak_1.png',
        'friend_request' || 'friend_accept' || 'group_request' || 'group' => 'assets/brand/mascot/prismo_group.png',
        'location' => 'assets/brand/mascot/prismo_explore.png',
        'exam' => 'assets/brand/mascot/prismo_graduate.png',
        _ => 'assets/brand/icons/bell.png',
      };

  Future<void> loadNotifications({bool silent = false}) async {
    if (!silent) isLoading.value = true;
    error.value = '';
    try {
      final list = await NotificationRepository.list();
      _raw
        ..clear()
        ..addEntries(list.map((n) => MapEntry('${n.id}', n)));
      actionStates.assignAll({for (final n in list) if (n.action != null && n.actionState != null) '${n.id}': n.actionState!});
      notifications.assignAll(list.map((n) {
        final route = n.route ?? '';
        final userMatch = RegExp(r'/community/users/(\d+)').firstMatch(route);
        return NotificationItem(
          id: '${n.id}',
          type: _type(n.kind),
          title: n.title,
          subtitle: n.body.isEmpty ? null : n.body,
          imagePath: n.image.isNotEmpty ? n.image : _defaultImage(n.kind),
          date: n.createdAt,
          isRead: n.read,
          hasAction: n.kind == 'follow' && n.action == null,
          actionText: n.kind == 'follow' ? 'Theo dõi lại' : null,
          targetUserId: userMatch?.group(1),
          payload: n.data,
        );
      }));
      RealtimeService.to.unreadNotifications.value = list.where((n) => !n.read).length;
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    } finally {
      isLoading.value = false;
    }
  }

  void _markLocal(String id) {
    final i = notifications.indexWhere((n) => n.id == id);
    if (i >= 0 && !notifications[i].isRead) {
      notifications[i] = notifications[i].copyWith(isRead: true);
      final unread = RealtimeService.to.unreadNotifications;
      if (unread.value > 0) unread.value--;
    }
  }

  Future<void> onNotificationTap(NotificationItem item) async {
    _markLocal(item.id);
    NotificationRepository.read(int.parse(item.id)).catchError((_) {});
    final route = _raw[item.id]?.route;
    if (route != null) await DeepLink.open(route);
  }

  Future<void> onActionTap(NotificationItem item) async {
    final uid = int.tryParse(item.targetUserId ?? '');
    if (uid == null) return;
    try {
      await CommunityRepository.follow(uid, true);
      Get.snackbar('Đã theo dõi', 'Bạn đã theo dõi lại người dùng này.', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  /// Đồng ý / Từ chối a friend request, or Duyệt / Từ chối someone asking into my group.
  Future<void> answer(NotificationItem item, bool yes) async {
    final n = _raw[item.id];
    if (n == null || answering.contains(item.id)) return;
    answering.add(item.id);
    try {
      if (n.action == 'friend_request') {
        await CommunityRepository.answerFriend(asInt(n.data['request_id']), yes);
      } else if (n.action == 'group_request') {
        await CommunityRepository.moderate(asInt(n.data['group_id']), asInt(n.data['member_id']), yes ? 'approve' : 'reject');
      }
      actionStates[item.id] = yes ? 'accepted' : 'gone';
      _markLocal(item.id);
      NotificationRepository.read(n.id).catchError((_) {});
      Get.snackbar(
          yes ? 'Xong' : 'Đã từ chối',
          n.action == 'friend_request' ? (yes ? 'Hai bạn đã là bạn bè.' : 'Người kia không nhận được thông báo.') : (yes ? 'Đã duyệt vào nhóm.' : 'Đã từ chối yêu cầu.'),
          snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
      loadNotifications(silent: true);
    } finally {
      answering.remove(item.id);
    }
  }

  Future<void> markAllAsRead() async {
    try {
      await NotificationRepository.readAll();
      notifications.assignAll(notifications.map((n) => n.copyWith(isRead: true)));
      RealtimeService.to.unreadNotifications.value = 0;
      Get.snackbar('Thành công', 'Đã đánh dấu tất cả thông báo là đã đọc', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }
}
