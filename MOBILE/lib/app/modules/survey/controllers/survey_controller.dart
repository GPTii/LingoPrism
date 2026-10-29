import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/services/auth_service.dart';

class SurveyController extends GetxController {
  static SurveyController get to => Get.find();

  // Current step (1-4)
  final _currentStep = 1.obs;
  int get currentStep => _currentStep.value;

  // Survey data
  final _name = ''.obs;
  final _birthDay = ''.obs;
  final _birthMonth = ''.obs;
  final _birthYear = ''.obs;
  final _gender = ''.obs;
  final _purpose = ''.obs;
  final _studyTime = ''.obs;
  final _language = ''.obs; // en | zh:hans | zh:hant | vi
  final _learnerType = 'adult'.obs;

  /// (value, label, subtitle)
  final languageOptions = const [
    ('en', 'Tiếng Anh', 'English'),
    ('zh:hans', 'Tiếng Trung giản thể', '简体中文 · chuẩn Trung Quốc đại lục · Pinyin'),
    ('zh:hant', 'Tiếng Trung phồn thể', '繁體中文 · chuẩn Đài Loan · Pinyin + Zhuyin'),
    ('vi', 'Tiếng Việt (cho bé)', 'Học từ vựng tiếng Việt qua hình ảnh'),
  ];

  String get language => _language.value;
  String get learnerType => _learnerType.value;
  void setLanguage(String v) {
    _language.value = v;
    if (v == 'vi') _learnerType.value = 'kid';
  }

  void setLearnerType(String v) => _learnerType.value = v;
  bool canContinueLanguage() => _language.value.isNotEmpty;

  // Text controllers
  final nameController = TextEditingController();

  // Getters
  String get name => _name.value;
  String get birthDay => _birthDay.value;
  String get birthMonth => _birthMonth.value;
  String get birthYear => _birthYear.value;
  String get gender => _gender.value;
  String get purpose => _purpose.value;
  String get studyTime => _studyTime.value;

  // Purpose options
  final purposeOptions = [
    'Không gì cả',
    'Học tập',
    'Công việc',
    'Giao tiếp hàng ngày',
    'Kết bạn bốn phương',
    'Khác',
  ];

  // Study time options
  final studyTimeOptions = [
    '5 phút/ngày',
    '10 phút/ngày',
    '15 phút/ngày',
    '20 phút/ngày',
  ];

  @override
  void onInit() {
    super.onInit();
    nameController.addListener(() {
      _name.value = nameController.text;
    });
  }

  @override
  void onClose() {
    nameController.dispose();
    super.onClose();
  }

  // Validation for each step
  bool canContinueStep1() {
    return _name.value.isNotEmpty &&
           _birthDay.value.isNotEmpty &&
           _birthMonth.value.isNotEmpty &&
           _birthYear.value.isNotEmpty &&
           _gender.value.isNotEmpty;
  }

  bool canContinueStep2() {
    return _purpose.value.isNotEmpty;
  }

  bool canContinueStep3() {
    return _studyTime.value.isNotEmpty;
  }

  // Navigation methods
  void nextStep() {
    if (_currentStep.value < 5) {
      _currentStep.value++;
    }
  }

  void previousStep() {
    if (_currentStep.value > 1) {
      _currentStep.value--;
    }
  }

  void goToStep(int step) {
    if (step >= 1 && step <= 5) {
      _currentStep.value = step;
    }
  }

  // Data setters
  void setName(String value) {
    _name.value = value;
  }

  void setBirthDay(String value) {
    _birthDay.value = value;
  }

  void setBirthMonth(String value) {
    _birthMonth.value = value;
  }

  void setBirthYear(String value) {
    _birthYear.value = value;
  }

  void setGender(String value) {
    _gender.value = value;
  }

  void setPurpose(String value) {
    _purpose.value = value;
  }

  void setStudyTime(String value) {
    _studyTime.value = value;
  }

  // Complete survey and navigate to home
  Future<void> completeSurvey() async {
    await _persistSurveyData();
    await AuthService.to.enterAfterSignIn(); // no picture yet: the profile screen asks for one
  }

  Future<void> _persistSurveyData() async {
    final parts = (_language.value.isEmpty ? 'en' : _language.value).split(':');
    final birthday = _buildBirthday();
    final minutes = int.tryParse(_studyTime.value.split(' ').first) ?? 10;
    const purposes = {
      'Công việc': 'work',
      'Học tập': 'study',
      'Giao tiếp hàng ngày': 'communication',
      'Kết bạn bốn phương': 'friends',
    };
    try {
      await AuthService.to.updateProfile({
        if (name.trim().isNotEmpty) 'display_name': name.trim(),
        if (birthday != null) 'birth_date': birthday.toIso8601String().substring(0, 10),
        if (gender.isNotEmpty) 'gender': {'Nam': 'male', 'Nữ': 'female'}[gender] ?? (['male', 'female'].contains(gender) ? gender : 'other'),
        'purpose': purposes[_purpose.value] ?? 'none',
        'daily_minutes': minutes,
        'active_language': parts.first,
        'learning_languages': [parts.first],
        if (parts.length > 1) 'zh_script': parts[1],
        if (parts.length > 1) 'show_zhuyin': parts[1] == 'hant',
        'learner_type': _learnerType.value,
        'onboarding_completed': true,
      });
    } catch (e) {
      Get.snackbar('Lỗi', 'Không lưu được thông tin khảo sát: $e', snackPosition: SnackPosition.BOTTOM);
      rethrow;
    }
  }

  DateTime? _buildBirthday() {
    if (_birthDay.isEmpty || _birthMonth.isEmpty || _birthYear.isEmpty) {
      return null;
    }
    final day = int.tryParse(_birthDay.value);
    final month = int.tryParse(_birthMonth.value);
    final year = int.tryParse(_birthYear.value);
    if (day == null || month == null || year == null) return null;
    return DateTime(year, month, day);
  }
}
