import 'package:get/get.dart';
import '../modules/exams/exams_module.dart';
import '../modules/stats/stats_module.dart';
import '../modules/speak/speak_module.dart';
import '../modules/live_camera/live_camera_module.dart';
import '../modules/photo_dialogue/photo_dialogue_module.dart';
import '../modules/photo_history/photo_history_module.dart';
import '../modules/levels/levels_module.dart';
import '../modules/literacy/literacy_module.dart';
import '../modules/sentence_practice/sentence_practice_module.dart';
import '../modules/poi_map/poi_map_module.dart';
import '../modules/messages/messages_module.dart';
import '../modules/social/social_module.dart';
import '../modules/support_chat/support_chat_module.dart';
import '../modules/splash/bindings/splash_binding.dart';
import '../modules/splash/views/splash_view.dart';
import '../modules/onboarding/bindings/onboarding_binding.dart';
import '../modules/onboarding/views/onboarding_view.dart';
import '../modules/login/bindings/login_binding.dart';
import '../modules/login/views/login_view.dart';
import '../modules/register/bindings/register_binding.dart';
import '../modules/register/views/register_view.dart';
import '../modules/survey/bindings/survey_binding.dart';
import '../modules/survey/views/survey_view.dart';
import '../modules/forgot_password/bindings/forgot_password_binding.dart';
import '../modules/forgot_password/views/forgot_password_view.dart';
import '../modules/forgot_password/views/verify_code_view.dart';
import '../modules/forgot_password/views/new_password_view.dart';
import '../modules/home/bindings/home_binding.dart';
import '../modules/home/views/home_view.dart';
import '../modules/shop/bindings/shop_binding.dart';
import '../modules/shop/views/shop_view.dart';
import '../modules/streak/bindings/streak_binding.dart';
import '../modules/streak/views/streak_view.dart';
import '../modules/notification/bindings/notification_binding.dart';
import '../modules/notification/views/notification_view.dart';
import '../modules/review/bindings/review_binding.dart';
import '../modules/review/views/review_view.dart';
import '../modules/community/bindings/community_binding.dart';
import '../modules/community/views/community_view.dart';
import '../modules/vocabulary_topic/bindings/vocabulary_topic_binding.dart';
import '../modules/vocabulary_topic/views/vocabulary_topic_view.dart';
import '../modules/vocabulary_list/bindings/vocabulary_list_binding.dart';
import '../modules/vocabulary_list/views/vocabulary_list_view.dart';
import '../modules/camera_detection/bindings/camera_detection_binding.dart';
import '../modules/camera_detection/views/camera_detection_view.dart';
import '../modules/camera_detection/views/detection_result_view.dart';
import '../modules/profile/bindings/profile_binding.dart';
import '../modules/profile/views/profile_view.dart';
import '../modules/profile_settings/bindings/profile_settings_binding.dart';
import '../modules/profile_settings/views/profile_settings_view.dart';
import '../modules/profile_edit/bindings/profile_edit_binding.dart';
import '../modules/profile_edit/views/profile_edit_view.dart';
import '../modules/profile_goal/bindings/profile_goal_binding.dart';
import '../modules/profile_goal/views/profile_goal_view.dart';
import '../modules/profile_change_password/bindings/profile_change_password_binding.dart';
import '../modules/profile_change_password/views/profile_change_password_view.dart';
import '../modules/profile_notification/bindings/profile_notification_binding.dart';
import '../modules/profile_notification/views/profile_notification_view.dart';
import '../modules/profile_guide/bindings/profile_guide_binding.dart';
import '../modules/profile_guide/views/profile_guide_view.dart';
import '../modules/community_member_profile/bindings/community_member_profile_binding.dart';
import '../modules/community_member_profile/views/community_member_profile_view.dart';
import '../modules/community_detail/bindings/community_detail_binding.dart';
import '../modules/community_detail/views/community_detail_view.dart';
import '../modules/community_chat/bindings/community_chat_binding.dart';
import '../modules/community_chat/views/community_chat_view.dart';
import '../modules/community_create_group/bindings/community_create_group_binding.dart';
import '../modules/community_create_group/views/community_create_group_view.dart';
import '../modules/add_vocabulary_category/bindings/add_vocabulary_category_binding.dart';
import '../modules/add_vocabulary_category/views/add_vocabulary_category_view.dart';
import '../modules/learning_session/bindings/learning_session_binding.dart';
import '../modules/learning_session/views/learning_session_view.dart';
import '../modules/vocabulary_flashcard/bindings/vocabulary_flashcard_binding.dart';
import '../modules/vocabulary_flashcard/views/vocabulary_flashcard_view.dart';

part 'app_routes.dart';

class AppPages {
  AppPages._();

  static const initial = Routes.splash;

  static final routes = [
    GetPage(
      name: _Paths.splash,
      page: () => const SplashView(),
      binding: SplashBinding(),
    ),
    GetPage(
      name: _Paths.onboarding,
      page: () => const OnboardingView(),
      binding: OnboardingBinding(),
    ),
    // Add other pages here
    GetPage(
      name: _Paths.home,
      page: () => const HomeView(),
      binding: HomeBinding(),
    ),
    GetPage(
      name: _Paths.login,
      page: () => const LoginView(),
      binding: LoginBinding(),
    ),
    GetPage(
      name: _Paths.register,
      page: () => const RegisterView(),
      binding: RegisterBinding(),
    ),
    GetPage(
      name: _Paths.survey,
      page: () => const SurveyView(),
      binding: SurveyBinding(),
    ),
    GetPage(
      name: _Paths.forgotPassword,
      page: () => const ForgotPasswordView(),
      binding: ForgotPasswordBinding(),
    ),
    GetPage(
      name: _Paths.verifyResetCode,
      page: () => const VerifyCodeView(),
      binding: ForgotPasswordBinding(),
    ),
    GetPage(
      name: _Paths.newPassword,
      page: () => const NewPasswordView(),
      binding: ForgotPasswordBinding(),
    ),
    GetPage(
      name: _Paths.shop,
      page: () => const ShopView(),
      binding: ShopBinding(),
    ),
    GetPage(
      name: _Paths.streak,
      page: () => const StreakView(),
      binding: StreakBinding(),
    ),
    GetPage(
      name: _Paths.notification,
      page: () => const NotificationView(),
      binding: NotificationBinding(),
    ),
    GetPage(
      name: _Paths.profile,
      page: () => const ProfileView(),
      binding: ProfileBinding(),
    ),
    GetPage(
      name: _Paths.profileSettings,
      page: () => const ProfileSettingsView(),
      binding: ProfileSettingsBinding(),
    ),
    GetPage(
      name: _Paths.profileEdit,
      page: () => const ProfileEditView(),
      binding: ProfileEditBinding(),
    ),
    GetPage(
      name: _Paths.profileGoal,
      page: () => const ProfileGoalView(),
      binding: ProfileGoalBinding(),
    ),
    GetPage(
      name: _Paths.profileChangePassword,
      page: () => const ProfileChangePasswordView(),
      binding: ProfileChangePasswordBinding(),
    ),
    GetPage(
      name: _Paths.profileNotification,
      page: () => const ProfileNotificationView(),
      binding: ProfileNotificationBinding(),
    ),
    GetPage(
      name: _Paths.profileGuide,
      page: () => const ProfileGuideView(),
      binding: ProfileGuideBinding(),
    ),
    GetPage(
      name: _Paths.community,
      page: () => const CommunityView(),
      binding: CommunityBinding(),
    ),
    GetPage(
      name: _Paths.communityDetail,
      page: () => const CommunityDetailView(),
      binding: CommunityDetailBinding(),
    ),
    GetPage(
      name: _Paths.communityChat,
      page: () => const CommunityChatView(),
      binding: CommunityChatBinding(),
    ),
    GetPage(
      name: _Paths.communityCreateGroup,
      page: () => const CommunityCreateGroupView(),
      binding: CommunityCreateGroupBinding(),
    ),
    GetPage(
      name: _Paths.addVocabularyCategory,
      page: () => const AddVocabularyCategoryView(),
      binding: AddVocabularyCategoryBinding(),
    ),
    GetPage(
      name: _Paths.communityMemberProfile,
      page: () => const CommunityMemberProfileView(),
      binding: CommunityMemberProfileBinding(),
    ),
    GetPage(
      name: _Paths.vocabularyTopic,
      page: () => const VocabularyTopicView(),
      binding: VocabularyTopicBinding(),
    ),
    GetPage(
      name: _Paths.review,
      page: () => const ReviewView(),
      binding: ReviewBinding(),
    ),
    GetPage(
      name: _Paths.vocabularyList,
      page: () => const VocabularyListView(),
      binding: VocabularyListBinding(),
    ),
    GetPage(
      name: _Paths.vocabularyFlashcard,
      page: () => const VocabularyFlashcardView(),
      binding: VocabularyFlashcardBinding(),
    ),
    GetPage(
      name: _Paths.learningSession,
      page: () => const LearningSessionView(),
      binding: LearningSessionBinding(),
    ),
    GetPage(
      name: _Paths.cameraDetection,
      page: () => const CameraDetectionView(),
      binding: CameraDetectionBinding(),
    ),
    GetPage(
      name: _Paths.detectionResult,
      page: () => const DetectionResultView(),
    ),
      GetPage(name: _Paths.stats, page: () => const StatsView()),
      GetPage(name: _Paths.speakPractice, page: () => const SpeakPracticeView()),
      GetPage(name: _Paths.liveCamera, page: () => const LiveCameraView()),
      GetPage(name: _Paths.photoDialogue, page: () => const PhotoDialogueView()),
      GetPage(name: _Paths.photoHistory, page: () => const PhotoHistoryView()),
      GetPage(name: _Paths.photoShot, page: () => const PhotoShotView()),
      GetPage(name: _Paths.examList, page: () => const ExamListView(), binding: BindingsBuilder(() => Get.lazyPut(() => ExamListController()))),
    GetPage(name: _Paths.examTake, page: () => const ExamTakeView(), binding: BindingsBuilder(() => Get.lazyPut(() => ExamTakeController()))),
    GetPage(name: _Paths.examResult, page: () => const ExamResultView(), binding: BindingsBuilder(() => Get.lazyPut(() => ExamResultController()))),
    GetPage(name: _Paths.sentencePractice, page: () => const SentencePracticeView(), binding: BindingsBuilder(() => Get.lazyPut(() => SentencePracticeController()))),
    GetPage(name: _Paths.literacyMap, page: () => const LiteracyMapView(), binding: BindingsBuilder(() => Get.lazyPut(() => LiteracyMapController()))),
    GetPage(name: _Paths.literacyLesson, page: () => const LiteracyLessonView(), binding: BindingsBuilder(() => Get.lazyPut(() => LiteracyLessonController()))),
    GetPage(name: _Paths.levelPath, page: () => const LevelPathView(), binding: BindingsBuilder(() => Get.put(LevelPathController(), permanent: true))),
    GetPage(name: _Paths.levelTest, page: () => const LevelTestView(), binding: BindingsBuilder(() => Get.lazyPut(() => LevelTestController()))),
    GetPage(name: _Paths.supportChat, page: () => const SupportChatView(), binding: BindingsBuilder(() => Get.lazyPut(() => SupportChatController()))),
    GetPage(name: _Paths.messages, page: () => const MessagesView(), binding: BindingsBuilder(() => Get.lazyPut(() => MessagesController()))),
    GetPage(name: _Paths.directChat, page: () => const DirectChatView(), binding: BindingsBuilder(() => Get.lazyPut(() => DirectChatController()))),
    GetPage(name: _Paths.poiMap, page: () => const PoiMapView(), binding: BindingsBuilder(() => Get.lazyPut(() => PoiMapController()))),
    GetPage(name: _Paths.friends, page: () => const FriendsView(), binding: BindingsBuilder(() => Get.lazyPut(() => FriendsController()))),
    GetPage(name: _Paths.savedPosts, page: () => const SavedPostsView(), binding: BindingsBuilder(() => Get.lazyPut(() => SavedPostsController()))),
  ];
}
