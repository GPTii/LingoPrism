import 'common.dart';
import 'vocab.dart';

class DetectedItem {
  DetectedItem({required this.id, required this.label, required this.confidence, required this.bbox, this.card,
      this.selected = false, this.feedback = 'unknown'});

  final int id;
  final String label;
  final double confidence;
  final List<double> bbox; // normalized x1, y1, x2, y2
  final WordCard? card;
  bool selected;
  String feedback; // unknown | correct | wrong

  factory DetectedItem.fromJson(Map<String, dynamic> j) => DetectedItem(
        id: asInt(j['id']),
        label: asString(j['label']),
        confidence: asDouble(j['confidence']),
        bbox: (j['bbox'] as List? ?? const []).map((e) => asDouble(e)).toList(),
        card: j['card'] is Map ? WordCard.fromJson(asMap(j['card'])) : null,
        selected: j['selected'] == true,
        feedback: asString(j['feedback'], 'unknown'),
      );
}

class DetectionResult {
  DetectionResult({required this.id, required this.model, required this.device, this.inferenceMs, this.image, required this.items});

  final int id;
  final String model;
  final String device;
  final int? inferenceMs;
  final String? image;
  final List<DetectedItem> items;

  factory DetectionResult.fromJson(Map<String, dynamic> j) => DetectionResult(
        id: asInt(j['id']),
        model: asString(j['model']),
        device: asString(j['device']),
        inferenceMs: j['inference_ms'] == null ? null : asInt(j['inference_ms']),
        image: j['image'] as String?,
        items: asMapList(j['items']).map(DetectedItem.fromJson).toList(),
      );
}

class Poi {
  Poi({required this.id, required this.name, required this.category, required this.categoryLabel, required this.lat,
      required this.lng, this.radiusM = 150, this.address = '', this.distanceM, this.topics = const []});

  final int id;
  final String name;
  final String category;
  final String categoryLabel;
  final double lat;
  final double lng;
  final int radiusM;
  final String address;
  final double? distanceM;
  final List<Map<String, dynamic>> topics; // {id, slug, name_vi, icon}

  factory Poi.fromJson(Map<String, dynamic> j) => Poi(
        id: asInt(j['id']),
        name: asString(j['name']),
        category: asString(j['category']),
        categoryLabel: asString(j['category_label']),
        lat: asDouble(j['lat']),
        lng: asDouble(j['lng']),
        radiusM: asInt(j['radius_m'], 150),
        address: asString(j['address']),
        distanceM: j['distance_m'] == null ? null : asDouble(j['distance_m']),
        topics: asMapList(j['topics_detail']),
      );
}

class ExamInfo {
  ExamInfo({required this.id, required this.title, this.description = '', required this.language, this.topicName,
      this.timeLimitMinutes, this.passPercent = 60, this.questionCount = 0, this.bestPercent, this.bestStatus, this.bestSubmission});

  final int id;
  final String title;
  final String description;
  final String language;
  final String? topicName;
  final int? timeLimitMinutes;
  final int passPercent;
  final int questionCount;
  final double? bestPercent;
  final String? bestStatus;
  final int? bestSubmission;

  factory ExamInfo.fromJson(Map<String, dynamic> j) {
    final best = j['my_best'] is Map ? asMap(j['my_best']) : null;
    return ExamInfo(
      id: asInt(j['id']),
      title: asString(j['title']),
      description: asString(j['description']),
      language: asString(j['language']),
      topicName: j['topic_name'] as String?,
      timeLimitMinutes: j['time_limit_minutes'] == null ? null : asInt(j['time_limit_minutes']),
      passPercent: asInt(j['pass_percent'], 60),
      questionCount: asInt(j['question_count']),
      bestPercent: best == null ? null : asDouble(best['percent']),
      bestStatus: best?['status'] as String?,
      bestSubmission: best == null ? null : asInt(best['submission']),
    );
  }
}

class ExamQuestion {
  ExamQuestion({required this.id, required this.kind, required this.prompt, this.imageUrl = '', this.options = const [], this.points = 1});

  final int id;
  final String kind; // mcq | fill | essay
  final String prompt;
  final String imageUrl;
  final List<String> options;
  final double points;

  factory ExamQuestion.fromJson(Map<String, dynamic> j) => ExamQuestion(
        id: asInt(j['id']),
        kind: asString(j['kind']),
        prompt: asString(j['prompt']),
        imageUrl: asString(j['image_url']),
        options: (j['options'] as List? ?? const []).map((e) => e.toString()).toList(),
        points: asDouble(j['points'], 1),
      );
}

class ExamAttempt {
  ExamAttempt({required this.submissionId, required this.title, required this.language, this.timeLimitMinutes, required this.startedAt, required this.questions});

  final int submissionId;
  final String title;
  final String language;
  final int? timeLimitMinutes;
  final DateTime startedAt;
  final List<ExamQuestion> questions;

  factory ExamAttempt.fromJson(Map<String, dynamic> j) => ExamAttempt(
        submissionId: asInt(j['submission']),
        title: asString(j['title']),
        language: asString(j['language']),
        timeLimitMinutes: j['time_limit_minutes'] == null ? null : asInt(j['time_limit_minutes']),
        startedAt: parseDate(j['started_at']) ?? DateTime.now(),
        questions: asMapList(j['questions']).map(ExamQuestion.fromJson).toList(),
      );
}

class AnswerResult {
  AnswerResult({required this.questionKind, required this.prompt, this.options = const [], this.correctOption, this.acceptedAnswers = const [],
      this.explanation = '', this.selectedOption, this.text = '', this.isCorrect, this.score, this.points = 1, this.feedback = ''});

  final String questionKind;
  final String prompt;
  final List<String> options;
  final int? correctOption;
  final List<String> acceptedAnswers;
  final String explanation;
  final int? selectedOption;
  final String text;
  final bool? isCorrect; // null = waiting for teacher
  final double? score;
  final double points;
  final String feedback;

  factory AnswerResult.fromJson(Map<String, dynamic> j) {
    final q = asMap(j['question']);
    return AnswerResult(
      questionKind: asString(q['kind']),
      prompt: asString(q['prompt']),
      options: (q['options'] as List? ?? const []).map((e) => e.toString()).toList(),
      correctOption: q['correct_option'] == null ? null : asInt(q['correct_option']),
      acceptedAnswers: (q['accepted_answers'] as List? ?? const []).map((e) => e.toString()).toList(),
      explanation: asString(q['explanation']),
      points: asDouble(q['points'], 1),
      selectedOption: j['selected_option'] == null ? null : asInt(j['selected_option']),
      text: asString(j['text']),
      isCorrect: j['is_correct'] as bool?,
      score: j['score'] == null ? null : asDouble(j['score']),
      feedback: asString(j['feedback']),
    );
  }
}

class SubmissionResult {
  SubmissionResult({required this.id, required this.examTitle, required this.status, this.score = 0, this.maxScore = 0,
      this.percent = 0, this.passed = false, this.feedback = '', this.answers = const []});

  final int id;
  final String examTitle;
  final String status; // submitted | graded
  final double score;
  final double maxScore;
  final double percent;
  final bool passed;
  final String feedback;
  final List<AnswerResult> answers;

  bool get waitingForTeacher => status == 'submitted';

  factory SubmissionResult.fromJson(Map<String, dynamic> j) => SubmissionResult(
        id: asInt(j['id']),
        examTitle: asString(j['exam_title']),
        status: asString(j['status']),
        score: asDouble(j['score']),
        maxScore: asDouble(j['max_score']),
        percent: asDouble(j['percent']),
        passed: j['passed'] == true,
        feedback: asString(j['feedback']),
        answers: asMapList(j['answers']).map(AnswerResult.fromJson).toList(),
      );
}
