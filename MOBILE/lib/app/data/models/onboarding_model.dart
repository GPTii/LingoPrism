class OnboardingModel {
  final String image;
  final String title;
  final String description;

  OnboardingModel({
    required this.image,
    required this.title,
    required this.description,
  });
}

final List<OnboardingModel> onboardingData = [
  OnboardingModel(
    image: 'assets/brand/mascot/prismo_camera.png',
    title: 'Chụp ảnh\nhọc từ vựng',
    description: 'Chụp hoặc chọn ảnh, LingoPrism tự phát hiện vật thể và gợi ý từ, phát âm, nghĩa, ví dụ. Chọn từ muốn lưu và gắn chú đề.',
  ),
  OnboardingModel(
    image: 'assets/brand/mascot/prismo_reminder.png',
    title: 'Học tập\nmọi lúc, mọi nơi',
    description: 'Không tiện học phát âm ở nơi đông người? Không có thời gian để hoàn thành bài học dài? Chúng tôi luôn có lựa chọn khác cho bạn!',
  ),
  OnboardingModel(
    image: 'assets/brand/mascot/prismo_group.png',
    title: 'Học cùng nhau\nđể bền bỉ mỗi ngày',
    description: 'Tham gia nhóm để cùng đạt mục tiêu, chia sẻ ảnh nhận diện và học từ vựng với bạn bè.',
  ),
];