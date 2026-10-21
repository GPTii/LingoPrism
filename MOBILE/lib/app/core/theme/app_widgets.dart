import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'app_colors.dart';

/// Reusable widgets for the app
class AppWidgets {
  AppWidgets._();

  /// Quest card gradient decoration
  ///
  /// Usage:
  /// ```dart
  /// Container(
  ///   decoration: AppWidgets.questGradientDecoration(),
  ///   child: ...,
  /// )
  /// ```
  static BoxDecoration questGradientDecoration() {
    // name kept for older screens: now the plain surface every card uses (a hairline, no gradient)
    return BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: AppColors.line),
    );
  }

  /// Standard action button used throughout the app
  ///
  /// Usage:
  /// ```dart
  /// AppWidgets.actionButton(
  ///   text: 'Chụp ảnh',
  ///   onPressed: () {},
  /// )
  /// ```
  static Widget actionButton({
    required String text,
    required VoidCallback onPressed,
  }) {
    return SizedBox(
      width: 124,
      height: 36,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          padding: EdgeInsets.zero,
          minimumSize: const Size(0, 36),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 0,
        ),
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  /// Primary continue/submit button used throughout the app
  ///
  /// Usage:
  /// ```dart
  /// AppWidgets.primaryButton(
  ///   text: 'Tiếp tục',
  ///   onPressed: canContinue ? () {} : null,
  ///   enabled: canContinue,
  /// )
  /// ```
  static Widget primaryButton({
    required String text,
    required VoidCallback? onPressed,
    bool enabled = true,
    double? width,
    bool isLoading = false,
  }) {
    return SizedBox(
      width: width ?? double.infinity,
      child: ElevatedButton(
        onPressed: enabled && !isLoading ? onPressed : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: enabled ? AppColors.buttonActive : AppColors.buttonDisabled,
          padding: const EdgeInsets.symmetric(vertical: 16),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          disabledBackgroundColor: AppColors.buttonDisabled,
        ),
        child: isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Text(
                text,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
              ),
      ),
    );
  }

  /// Show an information dialog
  ///
  /// Usage:
  /// ```dart
  /// AppWidgets.showInfoDialog(
  ///   title: 'Thông báo',
  ///   message: 'Nội dung thông báo',
  /// )
  /// ```
  static Future<void> showInfoDialog({
    required String title,
    required String message,
    String buttonText = 'OK',
    VoidCallback? onConfirm,
  }) async {
    await Get.dialog(
      AlertDialog(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        title: Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        content: Text(
          message,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 15,
            color: AppColors.textSecondary,
            height: 1.4,
          ),
        ),
        actionsAlignment: MainAxisAlignment.center,
        actionsPadding: const EdgeInsets.only(bottom: 20),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              onConfirm?.call();
            },
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
            ),
            child: Text(
              buttonText,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppColors.primary,
              ),
            ),
          ),
        ],
      ),
      barrierDismissible: false,
    );
  }

  /// Show an error dialog
  ///
  /// Usage:
  /// ```dart
  /// AppWidgets.showErrorDialog(
  ///   title: 'Lỗi kết nối',
  ///   message: 'Không thể kết nối đến server.',
  /// )
  /// ```
  static Future<void> showErrorDialog({
    String title = 'Lỗi',
    required String message,
    String buttonText = 'OK',
    VoidCallback? onConfirm,
  }) async {
    await Get.dialog(
      AlertDialog(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        title: Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        content: Text(
          message,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 15,
            color: AppColors.textSecondary,
            height: 1.4,
          ),
        ),
        actionsAlignment: MainAxisAlignment.center,
        actionsPadding: const EdgeInsets.only(bottom: 20),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              onConfirm?.call();
            },
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
            ),
            child: Text(
              buttonText,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppColors.error,
              ),
            ),
          ),
        ],
      ),
      barrierDismissible: false,
    );
  }

  /// Show a confirmation dialog with two buttons
  ///
  /// Usage:
  /// ```dart
  /// final result = await AppWidgets.showConfirmDialog(
  ///   title: 'Xác nhận',
  ///   message: 'Bạn có chắc chắn muốn thực hiện?',
  /// );
  /// if (result == true) {
  ///   // User confirmed
  /// }
  /// ```
  static Future<bool?> showConfirmDialog({
    required String title,
    required String message,
    String cancelText = 'Hủy',
    String confirmText = 'Xác nhận',
    Color? confirmColor,
  }) async {
    return await Get.dialog<bool>(
      AlertDialog(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        title: Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        content: Text(
          message,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 15,
            color: AppColors.textSecondary,
            height: 1.4,
          ),
        ),
        actionsAlignment: MainAxisAlignment.center,
        actionsPadding: const EdgeInsets.only(bottom: 20, left: 20, right: 20),
        actions: [
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Get.back(result: false),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    side: const BorderSide(color: AppColors.lineStrong, width: 1.5),
                  ),
                  child: Text(
                    cancelText,
                    style: const TextStyle(
                      fontSize: 16,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => Get.back(result: true),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: confirmColor ?? AppColors.buttonActive,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Text(
                    confirmText,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
      barrierDismissible: false,
    );
  }

  /// Show a success dialog
  ///
  /// Usage:
  /// ```dart
  /// AppWidgets.showSuccessDialog(
  ///   title: 'Thành công',
  ///   message: 'Đã lưu thông tin thành công',
  /// )
  /// ```
  static Future<void> showSuccessDialog({
    String title = 'Thành công',
    required String message,
    String buttonText = 'OK',
    VoidCallback? onConfirm,
  }) async {
    await Get.dialog(
      AlertDialog(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        title: Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        content: Text(
          message,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 15,
            color: AppColors.textSecondary,
            height: 1.4,
          ),
        ),
        actionsAlignment: MainAxisAlignment.center,
        actionsPadding: const EdgeInsets.only(bottom: 20),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              onConfirm?.call();
            },
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
            ),
            child: Text(
              buttonText,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppColors.success,
              ),
            ),
          ),
        ],
      ),
      barrierDismissible: false,
    );
  }

  /// Show a branded loading overlay with mascot image and message.
  ///
  /// Call `Get.back()` to close when loading completes.
  static Future<void> showLoadingOverlay({
    String message = 'Đang tải dữ liệu, vui lòng đợi...',
  }) async {
    // Avoid stacking multiple loading dialogs.
    if (Get.isDialogOpen == true) {
      Get.back<void>();
    }

    await Get.dialog(
      WillPopScope(
        onWillPop: () async => false,
        child: Center(
          child: Container(
            padding: const EdgeInsets.all(20),
            margin: const EdgeInsets.symmetric(horizontal: 32),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: AppColors.line),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image.asset(
                  'assets/brand/mascot/prismo_sleepy.png',
                  width: 96,
                  height: 96,
                  fit: BoxFit.contain,
                ),
                const SizedBox(height: 14),
                const CircularProgressIndicator(
                  strokeWidth: 3,
                  valueColor: AlwaysStoppedAnimation(AppColors.primary),
                ),
                const SizedBox(height: 12),
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.4,
                    fontWeight: FontWeight.w500,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      barrierDismissible: false,
      barrierColor: AppColors.ink.withValues(alpha: 0.35),
    );
  }
}
