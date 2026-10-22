import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../core/theme/app_colors.dart';
import '../../../data/models/api/common.dart';
import '../../../data/repositories/repositories.dart';
import '../../community_member_profile/controllers/community_member_profile_controller.dart';
import '../../messages/messages_module.dart' show avatarImage;

const _langName = {'en': 'tiếng Anh', 'zh': 'tiếng Trung', 'vi': 'tiếng Việt'};

/// "Gợi ý bạn học" at the top of the feed: learners of the same language first (server decides; never children,
/// staff, blocked people or people already followed). Following someone who follows you opens private messages.
class FollowSuggestions extends StatefulWidget {
  const FollowSuggestions({super.key});

  @override
  State<FollowSuggestions> createState() => _FollowSuggestionsState();
}

class _FollowSuggestionsState extends State<FollowSuggestions> {
  List<Map<String, dynamic>> _people = const [];
  final Set<int> _followed = {};

  @override
  void initState() {
    super.initState();
    ApiClient.to.get<dynamic>('/community/users/suggestions/').then((d) {
      if (mounted) setState(() => _people = asMapList(d));
    }).catchError((_) {});
  }

  Future<void> _follow(int id) async {
    try {
      await CommunityRepository.follow(id, true);
      setState(() => _followed.add(id));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_people.isEmpty) return const SizedBox();
    return Padding(
      padding: EdgeInsets.only(bottom: 16.h),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Gợi ý bạn học',
            style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
        SizedBox(height: 10.h),
        SizedBox(
          height: 168.h,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: _people.length,
            separatorBuilder: (_, __) => SizedBox(width: 10.w),
            itemBuilder: (_, i) {
              final p = _people[i];
              final author = Author.fromJson(p);
              final followsMe = p['follows_me'] == true;
              final done = _followed.contains(author.id);
              return Container(
                width: 132.w,
                padding: EdgeInsets.all(10.w),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(16.r),
                  border: Border.all(color: AppColors.line),
                ),
                child: Column(children: [
                  GestureDetector(
                    onTap: () => CommunityMemberProfileArguments.open(author.id,
                        displayName: author.displayName, avatar: author.avatarOrDefault),
                    child: Column(children: [
                      CircleAvatar(radius: 22.r, backgroundImage: avatarImage(author.avatarOrDefault)),
                      SizedBox(height: 6.h),
                      Text(author.displayName, maxLines: 1, overflow: TextOverflow.ellipsis,
                          style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                    ]),
                  ),
                  Text(followsMe ? 'Đang theo dõi bạn' : 'Học ${_langName[p['active_language']] ?? ''}',
                      maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary)),
                  const Spacer(),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: done ? null : () => _follow(author.id),
                      style: FilledButton.styleFrom(padding: EdgeInsets.zero, visualDensity: VisualDensity.compact),
                      child: Text(done ? 'Đã theo dõi' : followsMe ? 'Theo dõi lại' : 'Theo dõi'),
                    ),
                  ),
                ]),
              );
            },
          ),
        ),
      ]),
    );
  }
}
