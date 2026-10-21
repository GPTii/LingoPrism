import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_widgets.dart';
import '../../../data/models/api/game.dart' as api;
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';

class ShopController extends GetxController {
  final coins = 0.obs;
  final gems = 0.obs;
  final isLoading = false.obs;
  final isInitialized = false.obs;
  final myItems = <ShopItem>[].obs;
  final catalogue = <api.ShopItem>[].obs;

  @override
  void onInit() {
    super.onInit();
    refreshShopData();
  }

  Future<void> loadUserBalance() async {
    await GameService.to.refreshSummary();
    coins.value = GameService.to.scales;
    gems.value = GameService.to.gems;
  }

  Future<void> loadUserInventory() async {
    try {
      catalogue.assignAll(await GameRepository.shop());
      myItems.assignAll(catalogue.where((i) => i.owned > 0).map((i) => ShopItem(
            id: i.code, name: i.name, description: i.description, imagePath: i.image,
            price: i.price, isCoins: i.paidWithScales, quantity: i.owned)));
    } catch (e) {
      Get.log('Shop load error: $e');
    }
    isInitialized.value = true;
  }

  ShopItem? getInventoryItem(String code) => myItems.firstWhereOrNull((i) => i.id == code);

  /// Activate an XP boost from the inventory.
  Future<void> useItem(String code) async {
    final item = catalogue.firstWhereOrNull((i) => i.code == code);
    if (item == null) return;
    try {
      final r = await GameRepository.use(item.id);
      AppWidgets.showSuccessDialog(title: 'Đã kích hoạt', message: '${item.name}: x${r['multiplier']} XP');
      await refreshShopData();
    } catch (e) {
      AppWidgets.showErrorDialog(title: 'Không thể dùng', message: ApiClient.toApiException(e).message);
    }
  }

  Future<void> showPurchaseDialog({
    required String itemName,
    required String itemDescription,
    required int price,
    required bool isCoins,
    required String imagePath,
  }) async {
    final result = await Get.dialog<bool>(
      Dialog(
        backgroundColor: AppColors.primaryTint,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Item image
              Image.asset(
                imagePath,
                height: 80,
                errorBuilder: (context, error, stackTrace) {
                  return const Icon(Icons.inventory, size: 60);
                },
              ),
              const SizedBox(height: 16),
              // Item name
              Text(
                itemName,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              // Item description
              Text(
                itemDescription,
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              // Price
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Image.asset(
                    isCoins ? 'assets/brand/icons/scale.png' : 'assets/brand/icons/gem.png',
                    height: 30,
                    errorBuilder: (context, error, stackTrace) {
                      return Icon(
                        isCoins ? Icons.monetization_on : Icons.diamond,
                        size: 30,
                      );
                    },
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '$price',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: isCoins ? AppColors.lineStrong : AppColors.primary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              // Confirm message
              Text(
                'Bạn có muốn mua vật phẩm này không?',
                style: TextStyle(
                  fontSize: 16,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              // Buttons
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
                        side: BorderSide(color: AppColors.textHint),
                      ),
                      child: Text(
                        'Hủy',
                        style: TextStyle(
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
                        backgroundColor: AppColors.buttonActive,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text(
                        'Mua',
                        style: TextStyle(
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
        ),
      ),
      barrierDismissible: true,
    );

    if (result == true) {
      await purchaseItem(itemName, price, isCoins, imagePath: imagePath);
    }
  }

  // Purchase item
  Future<void> purchaseItem(String itemName, int price, bool isCoins, {String? imagePath}) async {
    if (!AuthService.to.isLoggedIn) {
      AppWidgets.showErrorDialog(title: 'Cần đăng nhập', message: 'Vui lòng đăng nhập để mua vật phẩm.');
      return;
    }
    if (catalogue.isEmpty) await loadUserInventory();
    final item = catalogue.firstWhereOrNull((i) => i.name == itemName || (imagePath != null && i.image == imagePath));
    if (item == null) {
      AppWidgets.showErrorDialog(title: 'Không thể mua', message: 'Vật phẩm không hợp lệ.');
      return;
    }
    try {
      final r = await GameRepository.buy(item.id);
      coins.value = (r['scales'] as num?)?.toInt() ?? coins.value;
      gems.value = (r['gems'] as num?)?.toInt() ?? gems.value;
      await loadUserInventory();
      GameService.to.refreshSummary();
      AppWidgets.showSuccessDialog(title: 'Thành công', message: 'Đã mua $itemName thành công!');
    } catch (e) {
      final err = ApiClient.toApiException(e);
      AppWidgets.showErrorDialog(title: err.message.startsWith('Không đủ') ? 'Không đủ tiền' : 'Lỗi', message: err.message);
    }
  }

  // Refresh balance and inventory
  Future<void> refreshShopData() async {
    isLoading.value = true;
    await loadUserBalance();
    await loadUserInventory();
    isLoading.value = false;
  }

}

/// Model for shop items
class ShopItem {
  const ShopItem({
    required this.id,
    required this.name,
    required this.description,
    required this.imagePath,
    required this.price,
    required this.isCoins,
    this.quantity = 0,
  });

  final String id;
  final String name;
  final String description;
  final String imagePath;
  final int price;
  final bool isCoins;
  final int quantity;

  ShopItem copyWith({
    String? id,
    String? name,
    String? description,
    String? imagePath,
    int? price,
    bool? isCoins,
    int? quantity,
  }) {
    return ShopItem(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      imagePath: imagePath ?? this.imagePath,
      price: price ?? this.price,
      isCoins: isCoins ?? this.isCoins,
      quantity: quantity ?? this.quantity,
    );
  }

  @override
  String toString() {
    return 'ShopItem(id: $id, name: $name, quantity: $quantity, price: $price)';
  }
}
