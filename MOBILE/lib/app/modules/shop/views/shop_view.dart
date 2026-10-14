import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../controllers/shop_controller.dart';
import '../../../core/theme/app_widgets.dart';

class ShopView extends GetView<ShopController> {
  const ShopView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE5FFFD),
      appBar: AppBar(
        backgroundColor: const Color(0xFFBBFFEE),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Get.back(),
        ),
        title: Text(
          'Cửa hàng',
          style: TextStyle(
            color: Colors.black,
            fontSize: 24.sp,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          // Coins
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 8.w),
            child: Row(
              children: [
                Image.asset(
                  'assets/images/vay.png',
                  width: 33.w,
                  height: 33.h,
                  errorBuilder: (context, error, stackTrace) {
                    return Icon(Icons.monetization_on, size: 32.sp);
                  },
                ),
                SizedBox(width: 4.w),
                Obx(() => Text(
                      '${controller.coins.value}',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16.sp,
                        color: const Color(0xFFB8C3D1),
                      ),
                    )),
              ],
            ),
          ),
          // Gems
          Padding(
            padding: EdgeInsets.only(right: 16.w),
            child: Row(
              children: [
                Image.asset(
                  'assets/images/ngoc.png',
                  width: 33.w,
                  height: 33.h,
                  errorBuilder: (context, error, stackTrace) {
                    return Icon(Icons.diamond, size: 32.sp);
                  },
                ),
                SizedBox(width: 4.w),
                Obx(() => Text(
                      '${controller.gems.value}',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16.sp,
                        color: const Color(0xFF0571E6),
                      ),
                    )),
              ],
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Vật phẩm của tôi
            Padding(
              padding: EdgeInsets.only(left: 20.w, top: 20.h, right: 20.w),
              child: Text(
                'Vật phẩm của tôi',
                style: TextStyle(
                  fontSize: 24.sp,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ),
            SizedBox(height: 16.h),
            Padding(
              padding: EdgeInsets.only(left: 12.w),
              child: _buildMyItems(),
            ),
            SizedBox(height: 24.h),

            // Mua ngay
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.w),
              child: Text(
                'Mua ngay',
                style: TextStyle(
                  fontSize: 24.sp,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ),
            SizedBox(height: 16.h),
            Padding(
              padding: EdgeInsets.only(left: 20.w, right: 20.w, bottom: 20.h),
              child: _buildShopItems(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMyItems() {
    return Obx(() {
      final items = controller.myItems;
      return SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: items
              .map(
                (item) => _buildMyItem(
                  item.imagePath,
                  item.name,
                  'x${item.quantity}',
                ),
              )
              .toList(),
        ),
      );
    });
  }

  Widget _buildMyItem(String imagePath, String title, String quantity) {
    final bool isOutOfStock = quantity == 'x0';

    return Container(
      height: 128.h,
      width: 128.w,
      margin: EdgeInsets.symmetric(horizontal: 6.w),
      padding: EdgeInsets.all(8.w),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(44.r),
      ),
      child: Column(
        children: [
          // Hình ảnh
          Image.asset(
            imagePath,
            height: 67.h,
            errorBuilder: (context, error, stackTrace) {
              return Icon(Icons.inventory, size: 50.sp);
            },
          ),
          SizedBox(height: 2.h),
          // Tên vật phẩm
          Text(
            title,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 12.sp,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 2.h),
          // Số lượng
          Text(
            quantity,
            style: TextStyle(
              fontSize: 12.sp,
              color: isOutOfStock ? Colors.grey : const Color(0xFF6B4EFF),
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildShopItems() {
    return Column(
      children: [
        _buildShopItem(
          'assets/images/XPx2.png',
          'Vảy tăng tốc',
          'Nhận đôi XP\nnhận được trong 15 phút',
          150,
          true,
        ),
        SizedBox(height: 12.h),
        _buildShopItem(
          'assets/images/streak/streakbang.png',
          'Đá băng',
          'Giữ chuỗi streak\nkhi nghỉ 1 ngày',
          200,
          true,
        ),
        SizedBox(height: 12.h),
        _buildShopItem(
          'assets/images/binhcucquang.png',
          'Bình cực quang',
          'Tăng 25% XP\ntoàn app trong 24 giờ',
          2,
          false,
        ),
        SizedBox(height: 12.h),
        _buildShopItem(
          'assets/images/chimcanhcut/chim_ok.png',
          'Sticker OK',
          'Dùng sticker trong\nchat nhóm & bình luận',
          2,
          false,
        ),
        SizedBox(height: 12.h),
        _buildShopItem(
          'assets/images/chimcanhcut/chim_yeu.png',
          'Sticker yêu ngất ngây',
          'Dùng sticker trong\nchat nhóm & bình luận',
          2,
          false,
        ),
        SizedBox(height: 12.h),
        _buildShopItem(
          'assets/images/chimcanhcut/chim_buon.png',
          'Sticker buồn hiu',
          'Dùng sticker trong\nchat nhóm & bình luận',
          2,
          false,
        ),
      ],
    );
  }

  Widget _buildShopItem(
    String imagePath,
    String title,
    String description,
    int price,
    bool isCoins,
  ) {
    return InkWell(
      onTap: () {
        controller.showPurchaseDialog(
          itemName: title,
          itemDescription: description,
          price: price,
          isCoins: isCoins,
          imagePath: imagePath,
        );
      },
      borderRadius: BorderRadius.circular(16.r),
      child: Container(
        padding: EdgeInsets.all(16.w),
        decoration: AppWidgets.questGradientDecoration(),
        child: Row(
          children: [
            // Item image
            SizedBox(
              child: Image.asset(
                imagePath,
                height: 67.h,
                errorBuilder: (context, error, stackTrace) {
                  return Icon(Icons.inventory, size: 40.sp);
                },
              ),
            ),
            SizedBox(width: 16.w),
            // Item info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 16.sp,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  SizedBox(height: 4.h),
                  Text(
                    description,
                    style: TextStyle(
                      fontSize: 12.sp,
                      color: Colors.black87,
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(width: 12.w),
            // Price
            Row(
              children: [
                Image.asset(
                  isCoins ? 'assets/images/vay.png' : 'assets/images/ngoc.png',
                  height: 35.h,
                ),
                SizedBox(width: 4.w),
                Text(
                  '$price',
                  style: TextStyle(
                    fontSize: 16.sp,
                    fontWeight: FontWeight.bold,
                    color: isCoins ? const Color(0xFFB8C3D1) : const Color(0xFF0571E6),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
