import 'dart:convert';

import '../../core/network/api_client.dart';
import '../models/api/common.dart';
import '../models/api/game.dart';
import '../models/api/learning_extra.dart';
import '../models/api/levels.dart';
import '../models/api/literacy.dart';
import '../models/api/sentence.dart';
import '../models/api/social.dart';
import '../models/api/user.dart';
import '../models/api/vocab.dart';
import '../services/offline_learning.dart';

ApiClient get _api => ApiClient.to;

/// Thin typed wrappers around the LingoPrism REST API (see BE Swagger at /api/docs/).
class AuthRepository {
  static Future<(AppUser, String, String)> login(String email, String password) async {
    final d = asMap(await _api.post('/auth/login/', data: {'email': email, 'password': password}, auth: false));
    return _session(d);
  }

  static Future<(AppUser, String, String)> register(String email, String password, String displayName) async {
    final d = asMap(await _api.post('/auth/register/',
        data: {'email': email, 'password': password, 'display_name': displayName}, auth: false));
    return _session(d);
  }

  static Future<(AppUser, String, String)> google(String idToken) async {
    final d = asMap(await _api.post('/auth/google/', data: {'id_token': idToken}, auth: false));
    return _session(d);
  }

  static (AppUser, String, String) _session(Map<String, dynamic> d) {
    final tokens = asMap(d['tokens']);
    return (AppUser.fromJson(asMap(d['user'])), asString(tokens['access']), asString(tokens['refresh']));
  }

  static Future<void> logout(String refresh) => _api.post('/auth/logout/', data: {'refresh': refresh});
  static Future<void> forgot(String email) => _api.post('/auth/password/forgot/', data: {'email': email}, auth: false);
  static Future<String> verify(String email, String code) async =>
      asString(asMap(await _api.post('/auth/password/verify/', data: {'email': email, 'code': code}, auth: false))['reset_token']);
  static Future<void> reset(String token, String password) =>
      _api.post('/auth/password/reset/', data: {'reset_token': token, 'new_password': password}, auth: false);
  static Future<void> changePassword(String oldPassword, String newPassword) =>
      _api.post('/auth/password/change/', data: {'old_password': oldPassword, 'new_password': newPassword});

  static Future<AppUser> me() async => AppUser.fromJson(asMap(await _api.get('/me/')));
  static Future<AppUser> updateMe(Map<String, dynamic> data) async => AppUser.fromJson(asMap(await _api.patch('/me/', data: data)));
  static Future<AppUser> uploadAvatar(String path) async =>
      AppUser.fromJson(asMap(await _api.upload('/me/', filePath: path, field: 'avatar', method: 'PATCH')));

  static Future<UserGoal> updateGoal(Map<String, dynamic> data) async => UserGoal.fromJson(asMap(await _api.patch('/me/goal/', data: data)));
}

class VocabRepository {
  static Future<List<Topic>> topics({bool mine = false}) async =>
      ApiClient.results(await _api.get('/topics/', query: {'page_size': 100, if (mine) 'mine': 1})).map(Topic.fromJson).toList();

  static Future<Topic> topic(int id) async => Topic.fromJson(asMap(await _api.get('/topics/$id/')));

  static Future<List<WordCard>> topicWords(int id) async =>
      ApiClient.results(await _api.get('/topics/$id/words/', query: {'page_size': 200})).map(WordCard.fromJson).toList();

  static Future<int> saveTopic(int id) async => asInt(asMap(await _api.post('/topics/$id/save/'))['added']);

  static Future<Topic> createTopic(String name, {String icon = '📘'}) async =>
      Topic.fromJson(asMap(await _api.post('/topics/', data: {'name_vi': name, 'icon': icon, 'visibility': 'private'})));

  static Future<void> deleteTopic(int id) => _api.delete('/topics/$id/');

  /// my own topic: put a word in it (also saved to my library) / take it out (it stays in my library)
  static Future<void> addToTopic(int topicId, int wordId) => _api.post('/topics/$topicId/words/$wordId/');
  static Future<void> removeFromTopic(int topicId, int wordId) => _api.delete('/topics/$topicId/words/$wordId/');

  static Future<List<WordCard>> search(String term) async =>
      ApiClient.results(await _api.get('/words/', query: {'search': term, 'page_size': 50})).map(WordCard.fromJson).toList();

  /// One page of verified words that have a translation in [lang] (the server lists checked data only).
  static Future<(int, List<WordCard>)> wordPage(String lang, String script, int page, {int pageSize = 50}) async {
    final d = asMap(await _api.get('/words/', query: {'lang': lang, 'script': script, 'page': page, 'page_size': pageSize}));
    return (asInt(d['count']), ApiClient.results(d).map(WordCard.fromJson).toList());
  }

  /// The same word seen through another language; null when it has no verified translation there.
  static Future<WordCard?> word(int id, String lang, {String? script}) async {
    try {
      return WordCard.fromJson(asMap(await _api.get('/words/$id/', query: {'lang': lang, 'script': script})));
    } catch (_) {
      return null;
    }
  }

  static Future<Map<String, WordCard>> byLabels(List<String> labels) async {
    final d = asMap(await _api.get('/words/by-labels/', query: {'labels': labels.join(',')}));
    return d.map((k, v) => MapEntry(k, WordCard.fromJson(asMap(v))));
  }

  static Future<void> report(int wordId, int? translationId, String reason, String details) =>
      _api.post('/reports/', data: {'word': wordId, 'translation': translationId, 'reason': reason, 'details': details});

  static Future<List<WordCard>> myWords({String? status, int? topic}) async => ApiClient.results(
          await _api.get('/my-words/', query: {'page_size': 200, 'status': status, 'topic': topic}))
      .map(WordCard.fromJson)
      .toList();

  static Future<List<WordCard>> dueWords() async =>
      ApiClient.results(await _api.get('/my-words/due/', query: {'page_size': 200})).map(WordCard.fromJson).toList();

  static Future<WordCard> addWord(int wordId, {String source = 'manual', int? topic, String sourceRef = ''}) async =>
      WordCard.fromJson(asMap(await _api.post('/my-words/', data: {'word': wordId, 'source': source, 'topic': topic, 'source_ref': sourceRef})));

  static Future<void> removeWord(int personalId) => _api.delete('/my-words/$personalId/');

  static Future<LibrarySummary> summary() async => LibrarySummary.fromJson(asMap(await _api.get('/my-words/summary/')));
}

class LearningRepository {
  /// A new session from the server; offline, the one kept on the phone (OfflineLearning) for a
  /// general learn / review lesson.
  static Future<StudySession> start(String kind, {int? topic, int? size}) async {
    try {
      return StudySession.fromJson(asMap(await _api.post('/sessions/', data: {'kind': kind, 'topic': topic, 'size': size})));
    } catch (e) {
      if (topic == null && OfflineLearning.isNetworkError(e)) {
        final kept = OfflineLearning.takeSession(kind);
        if (kept != null) return StudySession.fromJson(kept);
      }
      rethrow;
    }
  }

  /// Offline, the answer waits on the phone and is sent when the connection is back.
  static Future<void> answer(int sessionId, {required int personalWord, required String questionType, required bool correct,
      bool firstTry = true, bool graded = false, int? responseMs, String answer = ''}) async {
    final path = '/sessions/$sessionId/answer/';
    final data = <String, dynamic>{
      'personal_word': personalWord, 'question_type': questionType, 'correct': correct, 'first_try': firstTry,
      'graded': graded, 'response_ms': responseMs, 'answer': answer,
    };
    try {
      await _api.post(path, data: data);
    } catch (e) {
      if (!OfflineLearning.isNetworkError(e)) rethrow;
      await OfflineLearning.enqueue(path, data);
    }
  }

  /// Offline, "finish" is queued too and the summary comes back without XP (it arrives on sync).
  static Future<SessionSummary> finish(int sessionId) async {
    final path = '/sessions/$sessionId/finish/';
    try {
      await OfflineLearning.flush(); // answers first, then the finish
      return SessionSummary.fromJson(asMap(await _api.post(path)));
    } catch (e) {
      if (!OfflineLearning.isNetworkError(e)) rethrow;
      await OfflineLearning.enqueue(path, const {});
      return SessionSummary.fromJson(const {});
    }
  }
}

class GameRepository {
  static Future<GameSummary> summary() async => GameSummary.fromJson(asMap(await _api.get('/gamification/summary/')));

  static Future<List<DayProgress>> progress({DateTime? start, DateTime? end}) async {
    String? d(DateTime? x) => x?.toIso8601String().substring(0, 10);
    final list = await _api.get('/gamification/progress/', query: {'start': d(start), 'end': d(end)});
    return asMapList(list).map(DayProgress.fromJson).toList();
  }

  static Future<(List<DailyQuest>, MonthlyQuest)> quests() async {
    final d = asMap(await _api.get('/quests/today/'));
    return (asMapList(d['quests']).map(DailyQuest.fromJson).toList(), MonthlyQuest.fromJson(asMap(d['monthly'])));
  }

  /// (scales, gems): a gem comes with the last of the day's quests.
  static Future<(int, int)> claimQuest(int id) async {
    final r = asMap(await _api.post('/quests/$id/claim/'));
    return (asInt(r['scales']), asInt(r['gems']));
  }
  static Future<int> claimMonthly() async => asInt(asMap(await _api.post('/quests/monthly/claim/'))['gems']);

  static Future<List<BadgeInfo>> badges({int? userId}) async =>
      asMapList(await _api.get('/badges/', query: {'user': userId})).map(BadgeInfo.fromJson).toList();

  static Future<Leaderboard> leaderboard({String scope = 'league'}) async =>
      Leaderboard.fromJson(asMap(await _api.get('/leaderboard/', query: {'scope': scope})));

  static Future<List<ShopItem>> shop() async => asMapList(await _api.get('/shop/items/')).map(ShopItem.fromJson).toList();
  static Future<Map<String, dynamic>> buy(int itemId) async => asMap(await _api.post('/shop/items/$itemId/buy/'));
  static Future<Map<String, dynamic>> use(int itemId) async => asMap(await _api.post('/shop/items/$itemId/use/'));

  /// The stickers I can send (from the packs I own).
  static Future<List<StickerInfo>> stickers() async =>
      asMapList(await _api.get('/shop/items/stickers/')).map(StickerInfo.fromJson).toList();

  static Future<Map<String, dynamic>> userStats(int userId) async => asMap(await _api.get('/users/$userId/stats/'));

  /// my Prismo and its whole wardrobe
  static Future<Wardrobe> wardrobe() async => Wardrobe.fromJson(asMap(await _api.get('/mascot/')));
  static Future<Wardrobe> dress({String? name, bool? asAvatar, Map<String, String>? wearing}) async =>
      Wardrobe.fromJson(asMap(await _api.patch('/mascot/', data: {
        if (name != null) 'name': name,
        if (asAvatar != null) 'as_avatar': asAvatar,
        if (wearing != null) 'wearing': wearing,
      })));
  static Future<Wardrobe> buyOutfit(String code) async => Wardrobe.fromJson(asMap(await _api.post('/mascot/buy/', data: {'code': code})));
}

class NotificationRepository {
  static Future<List<AppNotification>> list() async =>
      ApiClient.results(await _api.get('/notifications/', query: {'page_size': 100})).map(AppNotification.fromJson).toList();
  static Future<int> unread() async => asInt(asMap(await _api.get('/notifications/unread-count/'))['unread']);
  static Future<void> read(int id) => _api.post('/notifications/$id/read/');
  static Future<void> readAll() => _api.post('/notifications/read-all/');
  static Future<Map<String, dynamic>> settings() async => asMap(await _api.get('/notification-settings/'));
  static Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> data) async =>
      asMap(await _api.patch('/notification-settings/', data: data));
}

class CommunityRepository {
  static Future<List<Post>> feed({int? userId, bool following = false, bool saved = false, int page = 1}) async => ApiClient.results(
          await _api.get('/posts/', query: {'user': userId, 'following': following ? 1 : null, 'saved': saved ? 1 : null, 'page': page}))
      .map(Post.fromJson)
      .toList();

  /// keep a post in "Bài đã lưu" / take it out
  static Future<void> bookmark(int id, bool save) => save ? _api.post('/posts/$id/bookmark/') : _api.delete('/posts/$id/bookmark/');

  /// the comment's writer or the post's author
  static Future<void> deleteComment(int postId, int commentId) => _api.delete('/posts/$postId/comments/$commentId/');

  // ---- friends

  /// by the 8-digit ID (exact) or by name (2+ letters)
  static Future<List<Person>> search(String q) async =>
      asMapList(await _api.get('/community/users/search/', query: {'q': q})).map(Person.fromJson).toList();
  static Future<List<Person>> friends() async =>
      asMapList(await _api.get('/community/users/friends/')).map(Person.fromJson).toList();

  /// incoming: waiting for my answer · outgoing: the ones I sent
  static Future<List<FriendRequestItem>> friendRequests({bool incoming = true}) async => asMapList(
          await _api.get('/community/users/friend-requests/', query: {'box': incoming ? 'incoming' : 'outgoing'}))
      .map(FriendRequestItem.fromJson)
      .toList();

  /// send a request with a hello – or accept theirs if they already asked
  static Future<FriendStatus> addFriend(int userId, {String message = ''}) async =>
      friendStatusFrom(asMap(await _api.post('/community/users/$userId/friend/', data: {'message': message}))['friend_status']);

  /// cancel my request, decline theirs, or unfriend
  static Future<void> removeFriend(int userId) => _api.delete('/community/users/$userId/friend/');
  static Future<FriendStatus> answerFriend(int requestId, bool accept) async => friendStatusFrom(
      asMap(await _api.post('/community/users/friend-requests/$requestId/${accept ? 'accept' : 'decline'}/'))['friend_status']);

  static Future<Post> post(int id) async => Post.fromJson(asMap(await _api.get('/posts/$id/')));

  static Future<Post> createPost(String imagePath, String caption, List<int> wordIds, {String topicLabel = ''}) async {
    return Post.fromJson(asMap(await _api.upload('/posts/', filePath: imagePath, fields: {
      'caption': caption,
      'topic_label': topicLabel,
      'word_ids': wordIds,
    })));
  }

  static Future<void> deletePost(int id) => _api.delete('/posts/$id/');
  static Future<void> like(int id, bool like) => like ? _api.post('/posts/$id/like/') : _api.delete('/posts/$id/like/');
  static Future<List<PostComment>> comments(int id) async =>
      asMapList(await _api.get('/posts/$id/comments/')).map(PostComment.fromJson).toList();
  static Future<PostComment> comment(int id, {String content = '', String? sticker}) async => PostComment.fromJson(asMap(await _api.post(
      '/posts/$id/comments/',
      data: sticker != null ? {'kind': 'sticker', 'sticker': sticker} : {'kind': 'text', 'content': content})));
  static Future<void> report(int id, String reason, String details) =>
      _api.post('/posts/$id/report/', data: {'reason': reason, 'details': details});
  static Future<int> saveWords(int id) async => asInt(asMap(await _api.post('/posts/$id/save-words/'))['added']);

  static Future<CommunityProfile> profile(int userId) async =>
      CommunityProfile.fromJson(asMap(await _api.get('/community/users/$userId/profile/')));
  static Future<void> follow(int userId, bool follow) =>
      follow ? _api.post('/community/users/$userId/follow/') : _api.delete('/community/users/$userId/follow/');

  /// Blocking also ends following both ways; no messages, no posts from each other.
  static Future<void> block(int userId, bool block) =>
      block ? _api.post('/community/users/$userId/block/') : _api.delete('/community/users/$userId/block/');

  /// Report a learner to the moderators; [thread] attaches that conversation's last messages as evidence.
  static Future<void> reportUser(int userId,
          {required String reason, String details = '', bool block = false, int? thread}) =>
      _api.post('/community/users/$userId/report/',
          data: {'reason': reason, 'details': details, 'block': block, if (thread != null) 'thread': thread});

  static Future<List<StudyGroup>> groups({bool mine = false, String? search}) async => ApiClient.results(
          await _api.get('/groups/', query: {'mine': mine ? 1 : null, 'search': search, 'page_size': 100}))
      .map(StudyGroup.fromJson)
      .toList();
  static Future<StudyGroup> group(int id) async => StudyGroup.fromJson(asMap(await _api.get('/groups/$id/')));
  static Future<StudyGroup> createGroup(String name, String description, bool requireApproval, {String icon = ''}) async =>
      StudyGroup.fromJson(asMap(await _api.post('/groups/',
          data: {'name': name, 'description': description, 'require_approval': requireApproval, 'icon': icon})));
  static Future<void> deleteGroup(int id) => _api.delete('/groups/$id/');
  static Future<String> join(int id, {String message = ''}) async =>
      asString(asMap(await _api.post('/groups/$id/join/', data: {'message': message}))['status']);
  static Future<void> leave(int id) => _api.post('/groups/$id/leave/');
  static Future<List<GroupMemberInfo>> members(int id) async =>
      asMapList(await _api.get('/groups/$id/members/')).map(GroupMemberInfo.fromJson).toList();
  static Future<void> moderate(int groupId, int memberId, String decision) =>
      _api.post('/groups/$groupId/members/$memberId/$decision/');
}

class ChatRepository {
  static Future<(List<ChatMessage>, bool)> groupMessages(int groupId, {int? before}) async {
    final d = asMap(await _api.get('/groups/$groupId/messages/', query: {'before': before}));
    return (asMapList(d['results']).map(ChatMessage.fromJson).toList(), d['has_more'] == true);
  }

  static Future<ChatMessage> sendGroup(int groupId, {String kind = 'text', String content = '', String sticker = '', String clientId = ''}) async =>
      ChatMessage.fromJson(asMap(await _api.post('/groups/$groupId/messages/',
          data: {'kind': kind, 'content': content, 'sticker': sticker, 'client_id': clientId})));

  static Future<SupportConversation> openSupport({String? content}) async =>
      SupportConversation.fromJson(asMap(await _api.post('/support/conversations/', data: {'content': content})));

  static Future<List<SupportConversation>> supportConversations() async =>
      ApiClient.results(await _api.get('/support/conversations/')).map(SupportConversation.fromJson).toList();

  static Future<List<ChatMessage>> supportMessages(int id) async =>
      asMapList(await _api.get('/support/conversations/$id/messages/')).map(ChatMessage.fromJson).toList();

  static Future<ChatMessage> sendSupport(int id, String content, {String clientId = ''}) async => ChatMessage.fromJson(
      asMap(await _api.post('/support/conversations/$id/messages/', data: {'content': content, 'client_id': clientId})));
}

class DetectionRepository {
  static Future<DetectionResult> detectOnServer(String imagePath, {String source = 'camera'}) async =>
      DetectionResult.fromJson(asMap(await _api.upload('/detect/', filePath: imagePath, fields: {'source': source})));

  /// A result the phone computed. With [imagePath] the photo goes along (items as JSON in the form): it then shows in
  /// the history like a server detection and the learners' error reports apply to it.
  static Future<DetectionResult> logOnDevice(String modelName, int inferenceMs, List<Map<String, dynamic>> items,
          {String? imagePath}) async =>
      DetectionResult.fromJson(asMap(imagePath == null
          ? await _api.post('/detections/log/', data: {'model_name': modelName, 'inference_ms': inferenceMs, 'items': items})
          : await _api.upload('/detections/log/', filePath: imagePath,
              fields: {'model_name': modelName, 'inference_ms': inferenceMs, 'items': jsonEncode(items)})));

  /// Returns (words saved, error reports remembered by the server).
  static Future<(int, int)> confirm(int detectionId, List<DetectedItem> items, {int? topic}) => confirmRaw(
      detectionId,
      items
          .map((i) => <String, dynamic>{
                'id': i.id,
                'selected': i.selected,
                'feedback': i.feedback,
                'corrected_label': i.picked ?? '',
                'not_object': i.notObject,
              })
          .toList(),
      topic: topic);

  static Future<(int, int)> confirmRaw(int detectionId, List<Map<String, dynamic>> items, {int? topic}) async {
    final d = asMap(await _api.post('/detections/$detectionId/confirm/', data: {'items': items, 'topic': topic}));
    return (asInt(d['saved']), asInt(d['reported']));
  }

  /// Every object the detector knows with its word card – the list for "it is something else".
  static Future<List<DetectionAlternative>> labels() async => (await labelsRaw())
      .map((j) => DetectionAlternative(label: asString(j['label']), confidence: 0, card: WordCard.fromJson(asMap(j['card']))))
      .toList();

  /// Same list as JSON, kept on the phone for detection without network (OfflineDetections).
  static Future<List<Map<String, dynamic>>> labelsRaw() async => asMapList(await _api.get('/detections/labels/'));

  /// The learner's photos, newest first: (page, has more). [confirmed] true/false keeps only photos with/without saved words.
  static Future<(List<DetectionResult>, bool)> history({int page = 1, bool? confirmed}) async {
    final d = await _api.get<dynamic>('/detections/', query: {'page': page, 'confirmed': confirmed == null ? null : (confirmed ? 1 : 0)});
    return (ApiClient.results(d).map(DetectionResult.fromJson).toList(), d is Map && d['next'] != null);
  }
}

class GisRepository {
  static Future<List<Poi>> nearby(double lat, double lng, {int radius = 3000}) async {
    final d = asMap(await _api.get('/pois-nearby/', query: {'lat': lat, 'lng': lng, 'radius': radius}));
    return asMapList(d['results']).map(Poi.fromJson).toList();
  }

  static Future<List<Map<String, dynamic>>> checkGeofence(double lat, double lng) async =>
      asMapList(asMap(await _api.post('/geofence/check/', data: {'lat': lat, 'lng': lng}))['entered']);
}

class ExamRepository {
  static Future<List<ExamInfo>> exams({String? language}) async =>
      ApiClient.results(await _api.get('/exams/', query: {'language': language, 'page_size': 100})).map(ExamInfo.fromJson).toList();

  static Future<ExamAttempt> start(int examId) async => ExamAttempt.fromJson(asMap(await _api.post('/exams/$examId/start/')));

  static Future<SubmissionResult> submit(int submissionId, List<Map<String, dynamic>> answers) async =>
      SubmissionResult.fromJson(asMap(await _api.post('/submissions/$submissionId/submit/', data: {'answers': answers})));

  static Future<SubmissionResult> result(int submissionId) async =>
      SubmissionResult.fromJson(asMap(await _api.get('/submissions/$submissionId/')));
}

class SentenceRepository {
  static Future<SentenceLesson> lesson({int? topic, int size = 10}) async =>
      SentenceLesson.fromJson(asMap(await _api.get('/sentences/lesson/', query: {'topic': topic, 'size': size})));

  static Future<SentenceCheck> check({required int sentence, required String type, required Object answer, required int responseMs}) async =>
      SentenceCheck.fromJson(asMap(await _api.post('/sentences/check/',
          data: {'sentence': sentence, 'type': type, 'answer': answer, 'response_ms': responseMs})));
}

class LiteracyRepository {
  static Future<List<LitLessonInfo>> lessons() async =>
      asMapList(asMap(await _api.get('/literacy/lessons/'))['lessons']).map(LitLessonInfo.fromJson).toList();

  static Future<LitLesson> lesson(int n) async => LitLesson.fromJson(asMap(await _api.get('/literacy/lessons/$n/')));

  static Future<LitCheck> check(String token, Object answer, int responseMs) async => LitCheck.fromJson(
      asMap(await _api.post('/literacy/check/', data: {'token': token, 'answer': answer, 'response_ms': responseMs})));

  static Future<LitFinish> finish(int n, String session, int total) async => LitFinish.fromJson(
      asMap(await _api.post('/literacy/lessons/$n/finish/', data: {'session': session, 'total': total})));
}

class LevelRepository {
  static Future<LevelProgress> progress() async => LevelProgress.fromJson(asMap(await _api.get('/levels/')));

  static Future<LevelProgress> choose(int level) async =>
      LevelProgress.fromJson(asMap(await _api.post('/levels/', data: {'level': level})));

  static Future<LevelTest> test(int level) async => LevelTest.fromJson(asMap(await _api.get('/levels/$level/test/')));

  static Future<LevelTestResult> submit(int level, String token, List<String> answers) async => LevelTestResult.fromJson(
      asMap(await _api.post('/levels/$level/test/', data: {'token': token, 'answers': answers})));
}
