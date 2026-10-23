import '../../core/widgets/prismo_avatar.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/navigation/back.dart';
import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/app_icon.dart';
import '../../core/widgets/prismo.dart';
import '../../data/models/api/common.dart';
import '../../data/models/api/social.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/auth_service.dart';
import '../../routes/app_pages.dart';
import '../community/controllers/community_controller.dart';
import '../community_detail/controllers/community_detail_controller.dart';
import '../community_member_profile/controllers/community_member_profile_controller.dart';
import '../../core/widgets/show_more.dart';

/// Friends (same server API as the web's /friends): every learner has an 8-digit ID to be found by; a friend
/// request carries a short hello and is answered by the other person (also from the notification). Adults only.

/// The friend button in its four states: "Kết bạn" (asks for a hello first), "Đã gửi lời mời" (can be cancelled),
/// "Đồng ý" / "Từ chối" when they asked me, and "Bạn bè" (can be ended).
class FriendButton extends StatefulWidget {
  const FriendButton({super.key, required this.userId, required this.name, required this.status, this.requestId,
      this.onChanged, this.compact = false});

  final int userId;
  final String name;
  final FriendStatus status;
  final int? requestId;
  final ValueChanged<FriendStatus>? onChanged;
  final bool compact;

  @override
  State<FriendButton> createState() => _FriendButtonState();
}

class _FriendButtonState extends State<FriendButton> {
  late FriendStatus _status = widget.status;
  bool _busy = false;

  @override
  void didUpdateWidget(covariant FriendButton old) {
    super.didUpdateWidget(old);
    if (old.status != widget.status) _status = widget.status;
  }

  Future<void> _run(Future<FriendStatus> Function() work, {String? done}) async {
    setState(() => _busy = true);
    try {
      final next = await work();
      if (!mounted) return;
      setState(() => _status = next);
      widget.onChanged?.call(next);
      if (done != null) Get.snackbar('Bạn bè', done, snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _ask() async {
    final me = AuthService.to.currentUser?.displayName ?? '';
    final text = TextEditingController(text: 'Chào ${widget.name}, mình là $me. Kết bạn cùng học nhé!');
    final send = await Get.bottomSheet<bool>(
      SafeArea(
        child: Container(
          padding: EdgeInsets.fromLTRB(20.w, 20.h, 20.w, 16.h + MediaQuery.of(context).viewInsets.bottom),
          decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.vertical(top: Radius.circular(24.r))),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Kết bạn với ${widget.name}', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
            SizedBox(height: 6.h),
            Text('Lời chào này gửi kèm thông báo tới ${widget.name}.', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
            SizedBox(height: 12.h),
            TextField(controller: text, maxLength: 200, maxLines: 4, minLines: 2, autofocus: true,
                decoration: const InputDecoration(border: OutlineInputBorder())),
            SizedBox(height: 8.h),
            SizedBox(
              width: double.infinity,
              child: FilledButton(onPressed: () => goBack(result: true), child: const Text('Gửi lời mời')),
            ),
          ]),
        ),
      ),
      isScrollControlled: true,
    );
    if (send == true) {
      await _run(() => CommunityRepository.addFriend(widget.userId, message: text.text.trim()),
          done: 'Đã gửi lời mời kết bạn tới ${widget.name}');
    }
  }

  Future<void> _remove({required String question, required String done}) async {
    final ok = await Get.dialog<bool>(AlertDialog(
      title: Text(question),
      actions: [
        TextButton(onPressed: () => goBack(result: false), child: const Text('Không')),
        TextButton(onPressed: () => goBack(result: true), child: Text('Đồng ý', style: TextStyle(color: AppColors.error))),
      ],
    ));
    if (ok == true) {
      await _run(() async {
        await CommunityRepository.removeFriend(widget.userId);
        return FriendStatus.none;
      }, done: done);
    }
  }

  Future<void> _answer(bool accept) => _run(
        () => widget.requestId != null
            ? CommunityRepository.answerFriend(widget.requestId!, accept)
            : CommunityRepository.addFriend(widget.userId),
        done: accept ? 'Bạn và ${widget.name} đã là bạn bè' : null,
      );

  @override
  Widget build(BuildContext context) {
    final dense = widget.compact
        ? const VisualDensity(horizontal: -2, vertical: -2)
        : VisualDensity.standard;
    if (_busy) {
      return SizedBox(width: 40.w, height: 32.h, child: const Center(child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))));
    }
    switch (_status) {
      case FriendStatus.incoming:
        return Row(mainAxisSize: MainAxisSize.min, children: [
          FilledButton(style: ButtonStyle(visualDensity: dense), onPressed: () => _answer(true), child: const Text('Đồng ý')),
          SizedBox(width: 6.w),
          OutlinedButton(style: ButtonStyle(visualDensity: dense), onPressed: () => _answer(false), child: const Text('Từ chối')),
        ]);
      case FriendStatus.outgoing:
        return OutlinedButton(
          style: ButtonStyle(visualDensity: dense),
          onPressed: () => _remove(question: 'Huỷ lời mời kết bạn gửi ${widget.name}?', done: 'Đã huỷ lời mời'),
          child: const Text('Đã gửi lời mời'),
        );
      case FriendStatus.friends:
        return OutlinedButton.icon(
          style: ButtonStyle(visualDensity: dense),
          onPressed: () => _remove(question: 'Huỷ kết bạn với ${widget.name}?', done: 'Đã huỷ kết bạn'),
          icon: const Icon(Icons.check_rounded, size: 18),
          label: const Text('Bạn bè'),
        );
      case FriendStatus.none:
        return FilledButton.icon(
          style: ButtonStyle(visualDensity: dense),
          onPressed: _ask,
          icon: const Icon(Icons.person_add_alt_1_rounded, size: 18),
          label: const Text('Kết bạn'),
        );
    }
  }
}

/// "ID của tôi": the 8 digits friends search for, with a copy button.
class MyIdCard extends StatelessWidget {
  const MyIdCard({super.key});

  @override
  Widget build(BuildContext context) {
    // Reactive: the cached user can predate public_id until /me/ comes back on app start.
    return Obx(() {
      final id = AuthService.to.user.value?.publicId ?? '';
      if (id.isEmpty) return const SizedBox.shrink();
      return _card(id);
    });
  }

  Widget _card(String id) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.line),
      ),
      child: Row(children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('ID của tôi', style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
            Text(id,
                style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w800, letterSpacing: 3, color: AppColors.textPrimary,
                    fontFeatures: const [FontFeature.tabularFigures()])),
          ]),
        ),
        OutlinedButton.icon(
          onPressed: () => copyPublicId(id, mine: true),
          icon: const Icon(Icons.copy_rounded, size: 18),
          label: const Text('Sao chép'),
        ),
      ]),
    );
  }
}

Future<void> copyPublicId(String id, {bool mine = false}) async {
  await Clipboard.setData(ClipboardData(text: id));
  Get.snackbar('Đã sao chép', mine ? 'Gửi ID $id cho bạn bè để họ tìm bạn.' : 'Đã sao chép ID $id.',
      snackPosition: SnackPosition.BOTTOM);
}

/// A small copy icon to sit next to someone's "ID 12345678".
class CopyIdButton extends StatelessWidget {
  const CopyIdButton({super.key, required this.id});

  final String id;

  @override
  Widget build(BuildContext context) => IconButton(
        onPressed: () => copyPublicId(id),
        icon: Icon(Icons.copy_rounded, size: 16.sp, color: AppColors.textSecondary),
        tooltip: 'Sao chép ID',
        visualDensity: VisualDensity.compact,
        padding: EdgeInsets.zero,
        constraints: BoxConstraints(minWidth: 32.w, minHeight: 32.w),
      );
}

/// One learner in a list, with the friend button on the right.
class PersonTile extends StatelessWidget {
  const PersonTile({super.key, required this.person, this.extra, this.onChanged});

  final Person person;
  final Widget? extra;
  final ValueChanged<FriendStatus>? onChanged;

  @override
  Widget build(BuildContext context) {
    final a = person.author;
    return InkWell(
      onTap: () => CommunityMemberProfileArguments.open(a.id, displayName: a.displayName, avatar: a.avatarOrDefault),
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
        child: Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
          PersonAvatar(avatar: a.avatar, look: a.mascot, size: 44.r),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(a.displayName, maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
              Text('ID ${a.publicId}', style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
              if (extra != null) extra!,
            ]),
          ),
          SizedBox(width: 8.w),
          FriendButton(userId: a.id, name: a.displayName, status: person.friendStatus, requestId: person.friendRequestId,
              onChanged: onChanged, compact: true),
        ]),
      ),
    );
  }
}

class FriendsController extends GetxController with GetSingleTickerProviderStateMixin {
  late final TabController tabs;
  final friends = <Person>[].obs;
  final incoming = <FriendRequestItem>[].obs;
  final outgoing = <FriendRequestItem>[].obs;
  final found = <Person>[].obs;
  final loading = false.obs;
  final searching = false.obs;
  final searched = ''.obs;

  @override
  void onInit() {
    super.onInit();
    final args = Get.arguments;
    tabs = TabController(length: 4, vsync: this, initialIndex: args is int ? args : 0);
    load();
  }

  @override
  void onClose() {
    tabs.dispose();
    super.onClose();
  }

  Future<void> load() async {
    loading.value = true;
    try {
      final r = await Future.wait([
        CommunityRepository.friends(),
        CommunityRepository.friendRequests(),
        CommunityRepository.friendRequests(incoming: false),
      ]);
      friends.assignAll(r[0] as List<Person>);
      incoming.assignAll(r[1] as List<FriendRequestItem>);
      outgoing.assignAll(r[2] as List<FriendRequestItem>);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      loading.value = false;
    }
  }

  Future<void> search(String q) async {
    final term = q.trim().replaceFirst('#', '');
    searched.value = term;
    if (term.length < 2) {
      found.clear();
      return;
    }
    searching.value = true;
    try {
      found.assignAll(await CommunityRepository.search(term));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      searching.value = false;
    }
  }
}

String _ago(DateTime t) {
  final d = DateTime.now().difference(t);
  if (d.inMinutes < 1) return 'vừa xong';
  if (d.inHours < 1) return '${d.inMinutes} phút trước';
  if (d.inDays < 1) return '${d.inHours} giờ trước';
  return '${d.inDays} ngày trước';
}

class FriendsView extends GetView<FriendsController> {
  const FriendsView({super.key});

  Widget _empty(String title, String body, PrismoMood mood) => ListView(children: [
        SizedBox(height: 40.h),
        Center(child: Prismo(mood: mood, size: 90.w)),
        SizedBox(height: 12.h),
        Text(title, textAlign: TextAlign.center, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 6.h),
          child: Text(body, textAlign: TextAlign.center, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
        ),
      ]);

  Widget _list(List<Widget> rows) => RefreshIndicator(
        onRefresh: controller.load,
        child: ListView(children: [
          ShowMoreColumn(limit: 10, divider: Divider(height: 1, color: AppColors.line), children: rows),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Bạn bè'),
        leading: const IconButton(icon: Icon(Icons.arrow_back), onPressed: goBack),
        bottom: TabBar(
          controller: controller.tabs,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: [
            Obx(() => Tab(text: 'Bạn bè${controller.friends.isEmpty ? '' : ' (${controller.friends.length})'}')),
            Obx(() => Tab(text: 'Lời mời${controller.incoming.isEmpty ? '' : ' (${controller.incoming.length})'}')),
            const Tab(text: 'Đã gửi'),
            const Tab(text: 'Tìm bạn'),
          ],
        ),
      ),
      body: Column(children: [
        Padding(padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 4.h), child: const MyIdCard()),
        Expanded(
          child: TabBarView(controller: controller.tabs, children: [
            Obx(() => controller.loading.value && controller.friends.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : controller.friends.isEmpty
                    ? _empty('Chưa có bạn bè', 'Vào "Tìm bạn", nhập ID hoặc tên để gửi lời mời kết bạn.', PrismoMood.wow)
                    : _list([
                        for (final p in controller.friends)
                          PersonTile(person: p, onChanged: (_) => controller.load()),
                      ])),
            Obx(() => controller.incoming.isEmpty
                ? _empty('Không có lời mời nào', 'Khi ai đó muốn kết bạn, lời mời hiện ở đây và trong Thông báo.', PrismoMood.sleepy)
                : _list([
                    for (final r in controller.incoming)
                      PersonTile(
                        person: r.person,
                        onChanged: (_) => controller.load(),
                        extra: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          if (r.message.isNotEmpty)
                            Padding(
                              padding: EdgeInsets.only(top: 4.h),
                              child: Text('“${r.message}”', style: TextStyle(fontSize: 13.sp, color: AppColors.textPrimary)),
                            ),
                          Text(_ago(r.createdAt), style: TextStyle(fontSize: 11.sp, color: AppColors.textHint)),
                        ]),
                      ),
                  ])),
            Obx(() => controller.outgoing.isEmpty
                ? _empty('Bạn chưa gửi lời mời nào', 'Lời mời đang chờ trả lời hiện ở đây, bạn có thể huỷ nếu muốn.', PrismoMood.happy)
                : _list([
                    for (final r in controller.outgoing)
                      PersonTile(
                        person: r.person,
                        onChanged: (_) => controller.load(),
                        extra: Text('Gửi ${_ago(r.createdAt)}', style: TextStyle(fontSize: 11.sp, color: AppColors.textHint)),
                      ),
                  ])),
            Column(children: [
              Padding(
                padding: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 8.h),
                child: TextField(
                  textInputAction: TextInputAction.search,
                  onSubmitted: controller.search,
                  decoration: InputDecoration(
                    hintText: 'Nhập ID 8 số hoặc tên bạn học',
                    prefixIcon: const Icon(Icons.search),
                    filled: true,
                    fillColor: AppColors.surface,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14.r)),
                  ),
                ),
              ),
              Expanded(
                child: Obx(() => controller.searching.value
                    ? const Center(child: CircularProgressIndicator())
                    : controller.searched.value.length < 2
                        ? _empty('Tìm bạn học', 'Hỏi ID của bạn mình (trong Hồ sơ hoặc Bạn bè) rồi nhập vào ô trên.', PrismoMood.think)
                        : controller.found.isEmpty
                            ? _empty('Không tìm thấy ai', 'Kiểm tra lại ID 8 số, hoặc thử tìm theo tên.', PrismoMood.sad)
                            : _list([for (final p in controller.found) PersonTile(person: p)])),
              ),
            ]),
          ]),
        ),
      ]),
    );
  }
}

/// "Bài đã lưu": the posts I bookmarked, newest saved first.
class SavedPostsController extends GetxController {
  final posts = <Post>[].obs;
  final loading = false.obs;

  @override
  void onInit() {
    super.onInit();
    load();
  }

  Future<void> load() async {
    loading.value = true;
    try {
      posts.assignAll(await CommunityRepository.feed(saved: true));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      loading.value = false;
    }
  }

  Future<void> unsave(Post p) async {
    try {
      await CommunityRepository.bookmark(p.id, false);
      posts.remove(p);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  void open(Post p) {
    final community = Get.isRegistered<CommunityController>() ? CommunityController.to : Get.put(CommunityController());
    Get.toNamed(Routes.communityDetail, arguments: CommunityDetailArguments(post: community.toPost(p)));
  }
}

class SavedPostsView extends GetView<SavedPostsController> {
  const SavedPostsView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Bài đã lưu'), leading: const IconButton(icon: Icon(Icons.arrow_back), onPressed: goBack)),
      body: Obx(() {
        if (controller.loading.value && controller.posts.isEmpty) return const Center(child: CircularProgressIndicator());
        if (controller.posts.isEmpty) {
          return ListView(children: [
            SizedBox(height: 60.h),
            Center(child: AppIcon('bookmark', size: 72.w)),
            SizedBox(height: 12.h),
            Text('Chưa lưu bài nào', textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 6.h),
              child: Text('Bấm "Lưu" dưới một bài viết trong Cộng đồng để xem lại ở đây.', textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
            ),
          ]);
        }
        return RefreshIndicator(
          onRefresh: controller.load,
          child: ListView.separated(
            padding: EdgeInsets.all(16.w),
            itemCount: controller.posts.length,
            separatorBuilder: (_, __) => SizedBox(height: 10.h),
            itemBuilder: (_, i) {
              final p = controller.posts[i];
              return Material(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16.r),
                child: InkWell(
                  borderRadius: BorderRadius.circular(16.r),
                  onTap: () => controller.open(p),
                  child: Padding(
                    padding: EdgeInsets.all(10.w),
                    child: Row(children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(12.r),
                        child: p.image.startsWith('http')
                            ? Image.network(p.image, width: 72.w, height: 72.w, fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => SizedBox(width: 72.w, height: 72.w))
                            : SizedBox(width: 72.w, height: 72.w),
                      ),
                      SizedBox(width: 12.w),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(p.author.displayName, style: TextStyle(fontSize: 14.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                          if (p.caption.isNotEmpty)
                            Text(p.caption, maxLines: 2, overflow: TextOverflow.ellipsis,
                                style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                          if (p.words.isNotEmpty)
                            Text(p.words.map((w) => w.text).take(4).join(' · '), maxLines: 1, overflow: TextOverflow.ellipsis,
                                style: TextStyle(fontSize: 12.sp, color: AppColors.primary, fontWeight: FontWeight.w600)),
                        ]),
                      ),
                      IconButton(
                        tooltip: 'Bỏ lưu',
                        onPressed: () => controller.unsave(p),
                        icon: const Icon(Icons.bookmark_rounded, color: Color(0xFFFFA800)),
                      ),
                    ]),
                  ),
                ),
              );
            },
          ),
        );
      }),
    );
  }
}

/// Author helper for other screens: the ID line under a name.
Widget publicIdLine(Author a) => a.publicId.isEmpty
    ? const SizedBox.shrink()
    : Text('ID ${a.publicId}', style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary));
