import 'package:get/get.dart';

/// Closes the top page, dialog or sheet. Use this instead of Get.back(): in GetX 4, while a snackbar is
/// showing, Get.back() only dismisses the snackbar and leaves the page where it is, so a back button
/// tapped right after a "saved" or error message seemed dead.
void goBack<T>({T? result}) {
  if (Get.isSnackbarOpen) Get.closeAllSnackbars();
  final nav = Get.key.currentState;
  if (nav != null && nav.canPop()) nav.pop<T>(result);
}
