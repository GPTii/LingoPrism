import 'package:flutter/material.dart';
import 'package:get/get.dart';

class IconCategory {
  final String label;
  final List<String> icons;

  const IconCategory({
    required this.label,
    required this.icons,
  });
}

class AddVocabularyCategoryController extends GetxController {
  AddVocabularyCategoryController();

  final TextEditingController nameController = TextEditingController();
  final RxnString selectedIcon = RxnString();
  final RxnString nameError = RxnString();
  final RxnString iconError = RxnString();
  final RxBool canSave = false.obs;

  final List<IconCategory> iconCategories = const [
    IconCategory(
      label: 'Con người',
      icons: [
        '👤',
        '🧒',
        '👩‍🎓',
        '👨‍🏫',
        '👩‍🍳',
        '👨‍💻',
        '🧑‍🎨',
        '🧑‍🔬',
      ],
    ),
    IconCategory(
      label: 'Động vật',
      icons: [
        '🐶',
        '🐱',
        '🐭',
        '🐹',
        '🐰',
        '🦊',
        '🦉',
        '🐢',
        '🐟',
        '🦋',
      ],
    ),
    IconCategory(
      label: 'Thức ăn & Đồ uống',
      icons: [
        '🍎',
        '🍇',
        '🍓',
        '🍉',
        '🌽',
        '🥕',
        '🍔',
        '🍕',
        '🍣',
        '🍩',
        '🍰',
        '🍪',
        '🍿',
        '🥤',
      ],
    ),
    IconCategory(
      label: 'Gia đình & Nhà cửa',
      icons: [
        '🏠',
        '🏡',
        '🏫',
        '🏥',
        '🛋️',
        '🛏️',
        '🛁',
        '🧸',
        '🪁',
        '🪑',
        '📦',
      ],
    ),
    IconCategory(
      label: 'Học tập & Công việc',
      icons: [
        '📚',
        '📖',
        '📒',
        '✏️',
        '📝',
        '🎓',
        '💼',
        '📊',
        '💡',
      ],
    ),
    IconCategory(
      label: 'Du lịch & Giao thông',
      icons: [
        '🌍',
        '🗺️',
        '🧭',
        '🚗',
        '🚲',
        '🛵',
        '🚌',
        '🚆',
        '✈️',
        '🚀',
        '⛵️',
      ],
    ),
    IconCategory(
      label: 'Thiên nhiên',
      icons: [
        '🌸',
        '🌹',
        '🌻',
        '🌵',
        '🌳',
        '🍁',
        '🌈',
        '🌙',
        '☀️',
        '⛄️',
      ],
    ),
    IconCategory(
      label: 'Giải trí',
      icons: [
        '🎮',
        '🕹️',
        '🎲',
        '🎳',
        '🎵',
        '🎷',
        '🎸',
        '🥁',
        '🎬',
        '📺',
        '📷',
      ],
    ),
    IconCategory(
      label: 'Thể thao & Sức khỏe',
      icons: [
        '⚽️',
        '🏀',
        '🏓',
        '🥊',
        '🏸',
        '🥇',
        '🧘',
        '🚴',
        '🏊',
      ],
    ),
    IconCategory(
      label: 'Khoa học & Sáng tạo',
      icons: [
        '🧪',
        '🔬',
        '⚙️',
        '🧬',
        '🧲',
        '🎨',
        '🧵',
        '✂️',
        '🖌️',
        '🧱',
      ],
    ),
  ];

  @override
  void onInit() {
    super.onInit();
    nameController.addListener(_updateCanSave);
    // If this controller is created with initial arguments (for editing),
    // populate fields.
    final args = Get.arguments;
    if (args is Map<String, dynamic>) {
      final name = args['name'] as String?;
      final icon = args['icon'] as String?;
      if (name != null && name.isNotEmpty) {
        nameController.text = name;
      }
      if (icon != null && icon.isNotEmpty) {
        selectedIcon.value = icon;
      }
      _updateCanSave();
    }
  }

  @override
  void onClose() {
    nameController.removeListener(_updateCanSave);
    nameController.dispose();
    super.onClose();
  }

  void openIconPicker() {
    final sheetHeight = Get.height * 0.75;
    Get.bottomSheet(
      Container(
        height: sheetHeight,
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
        child: SafeArea(
          top: false,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 48,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Chọn icon cho chủ đề',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: iconCategories.map((category) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              category.label,
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFF1F2937),
                              ),
                            ),
                            const SizedBox(height: 12),
                            GridView.builder(
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              gridDelegate:
                                  const SliverGridDelegateWithFixedCrossAxisCount(
                                crossAxisCount: 6,
                                mainAxisSpacing: 12,
                                crossAxisSpacing: 12,
                              ),
                              itemCount: category.icons.length,
                              itemBuilder: (context, index) {
                                final icon = category.icons[index];
                                final isSelected = selectedIcon.value == icon;
                                return GestureDetector(
                                  onTap: () {
                                    selectedIcon.value = icon;
                                    iconError.value = null;
                                    _updateCanSave();
                                    Get.back();
                                  },
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 200),
                                    decoration: BoxDecoration(
                                      color: isSelected
                                          ? const Color(0xFF1CB0F6)
                                              .withValues(alpha: 0.18)
                                          : const Color(0xFFF5F8FF),
                                      borderRadius: BorderRadius.circular(16),
                                      border: Border.all(
                                        color: isSelected
                                            ? const Color(0xFF1CB0F6)
                                            : Colors.transparent,
                                        width: 2,
                                      ),
                                    ),
                                    child: Center(
                                      child: Text(
                                        icon,
                                        style: const TextStyle(fontSize: 24),
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      isScrollControlled: true,
    );
  }

  void onSave() {
    final trimmedName = nameController.text.trim();
    var hasError = false;

    if (trimmedName.isEmpty) {
      nameError.value = 'Vui lòng nhập tên chủ đề';
      hasError = true;
    } else {
      nameError.value = null;
    }

    if (selectedIcon.value == null || selectedIcon.value!.isEmpty) {
      iconError.value = 'Vui lòng chọn icon';
      hasError = true;
    } else {
      iconError.value = null;
    }

    if (hasError) {
      return;
    }

    Get.back(result: {
      'name': trimmedName,
      'icon': selectedIcon.value!,
    });
  }

  void _updateCanSave() {
    final trimmedName = nameController.text.trim();
    canSave.value = trimmedName.isNotEmpty && selectedIcon.value != null;
  }
}
