import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:get/get.dart';
import '../../community/controllers/community_controller.dart';

class CommunityDetailArguments {
  const CommunityDetailArguments({required this.post});
  final CommunityPost post;
}

class CommunityDetailController extends GetxController {
  late CommunityPost post;
  final FlutterTts _tts = FlutterTts();

  @override
  void onInit() {
    super.onInit();
    final args = Get.arguments;
    if (args is CommunityDetailArguments) {
      post = args.post;
      if (Get.isRegistered<CommunityController>()) {
        Get.find<CommunityController>().refreshCommentsForPost(post);
      }
    } else {
      // Tránh gọi snackbar/back trong build: đợi sau frame đầu
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Get.snackbar('Lỗi', 'Không tìm thấy bài viết.');
        Get.back();
      });
      // Giữ một post rỗng để tránh crash render
      post = CommunityPost(
        id: '',
        authorId: '',
        authorName: '',
        authorAvatar: '',
        postedAt: '',
        imageUrl: '',
        vocabularyItems: const [],
        likes: 0,
        comments: 0,
        bookmarks: 0,
      );
    }
    _initTts();
  }

  @override
  void onClose() {
    _tts.stop();
    super.onClose();
  }

  Future<void> speakWord(String word) async {
    final trimmed = word.trim();
    if (trimmed.isEmpty) return;
    try {
      await _tts.stop();
      await _tts.speak(trimmed);
    } catch (e) {
      Get.log('CommunityDetailController speak error: $e');
      if (Get.isRegistered<CommunityController>()) {
        Get.find<CommunityController>().speakWord(trimmed);
      }
    }
  }

  Future<void> _initTts() async {
    try {
      await _tts.setLanguage('en-US');
      await _tts.setPitch(1.0);
      await _tts.setSpeechRate(0.45);
      await _tts.setVolume(1.0);
    } catch (e) {
      Get.log('CommunityDetailController TTS init error: $e');
    }
  }
}
