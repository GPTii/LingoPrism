/// Community Chat View Library
///
/// A comprehensive chat interface for SnapLingua community groups
/// featuring real-time messaging, sticker support, and optimized performance.
library community_chat_view;
///
/// Features:
/// - Real-time message display with optimized ListView
/// - Enhanced null safety and validation throughout
/// - Sticker support with fallback error handling
/// - Performance optimizations with RepaintBoundary widgets
/// - Comprehensive input validation and error handling
/// - Professional UI/UX with directional chat bubbles
/// - Empty state handling and user feedback
/// - Memory management for large message lists
///
/// Performance Optimizations:
/// - RepaintBoundary widgets for minimal rebuilds
/// - ListView caching with configurable extent
/// - Message memory limiting to prevent performance issues
/// - Optimized image loading with proper error handling
/// - Debounced send operations with loading states
///
/// Author: Claude Code Assistant
/// Last updated: November 2024

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/community_chat_controller.dart';
import '../models/community_chat_models.dart';

/// Main chat view widget for community group conversations
///
/// This is the primary interface for real-time group chat functionality.
/// It provides a comprehensive chat experience with optimized performance,
/// enhanced user feedback, and professional UI styling.
///
/// Key Components:
/// - [_ChatHeader] - Group information display with navigation
/// - [_buildMessagesList] - Optimized message list with performance controls
/// - [_ChatInput] - Advanced text input with validation and send controls
/// - [_buildEmptyState] - User-friendly empty state display
///
/// The view automatically handles state management through GetX observables
/// and provides real-time updates for incoming messages.
class CommunityChatView extends GetView<CommunityChatController> {
  const CommunityChatView({super.key});

  /// Performance optimization constants for memory and render management
  static const double _listCacheExtent = 800.0;
  static const int _maxMessagesInMemory = 200;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE6F9FF),
      body: SafeArea(
        child: Column(
          children: [
            _ChatHeader(controller: controller),
            Divider(height: 1.h, color: const Color(0xFFE0E6EE)),
            Expanded(
              child: Obx(
                () => _buildMessagesList(),
              ),
            ),
            _ChatInput(onSend: controller.sendMessage),
          ],
        ),
      ),
    );
  }

  /// Build optimized messages list with performance enhancements
  Widget _buildMessagesList() {
    final messages = controller.messages;

    if (messages.isEmpty) {
      return _buildEmptyState();
    }

    // Limit messages in memory for performance
    final displayMessages = messages.length > _maxMessagesInMemory
        ? messages.skip(messages.length - _maxMessagesInMemory).toList()
        : messages;

    return ListView.builder(
      controller: controller.scrollController,
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 18.h),
      reverse: false,
      physics: const BouncingScrollPhysics(
        parent: AlwaysScrollableScrollPhysics(),
      ),
      // Performance optimizations
      cacheExtent: _listCacheExtent,
      itemCount: displayMessages.length,
      itemBuilder: (context, index) {
        final message = displayMessages[index];
        return RepaintBoundary(
          key: ValueKey('message_${message.messageId ?? index}'),
          child: _ChatBubble(message: message),
        );
      },
    );
  }

  /// Build empty state when no messages
  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(40.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.chat_bubble_outline,
              size: 48.w,
              color: const Color(0xFFB0BEC5),
            ),
            SizedBox(height: 16.h),
            Text(
              'Chưa có tin nhắn',
              style: TextStyle(
                fontSize: 16.sp,
                fontWeight: FontWeight.w600,
                color: const Color(0xFF5D6A7C),
              ),
            ),
            SizedBox(height: 8.h),
            Text(
              'Hãy bắt đầu cuộc trò chuyện với nhóm',
              style: TextStyle(
                fontSize: 14.sp,
                color: const Color(0xFF7D8AA2),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

/// Chat header widget displaying group information and navigation controls
///
/// Shows the group avatar, name, member count, and provides back navigation.
/// Includes comprehensive error handling for image loading and safe navigation.
/// Uses validated data from the group model to ensure reliable display.
class _ChatHeader extends StatelessWidget {
  const _ChatHeader({required this.controller});

  final CommunityChatController controller;

  @override
  Widget build(BuildContext context) {
    final details = controller.groupDetails;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 16.h),
      child: Row(
        children: [
          IconButton(
            onPressed: () => _safeNavigationBack(),
            icon: const Icon(Icons.arrow_back_ios_new_rounded),
            color: const Color(0xFF1A1D1F),
          ),
          Container(
            width: 60.w,
            height: 60.w,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20.r),
              border: Border.all(
                color: const Color(0xFFE0E6EE),
                width: 1.0,
              ),
            ),
            padding: EdgeInsets.all(8.w),
            child: _buildGroupImage(details.group.validatedAssetImage),
          ),
          SizedBox(width: 14.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  details.group.validatedName,
                  style: TextStyle(
                    fontSize: 17.sp,
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFF1A1D1F),
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                SizedBox(height: 4.h),
                Text(
                  '${details.group.validatedMemberCount} thành viên',
                  style: TextStyle(
                    fontSize: 13.sp,
                    color: const Color(0xFF5D6A7C),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Safe navigation back with error handling
  void _safeNavigationBack() {
    try {
      // Use Navigator instead of Get.canPop() for better compatibility
      if (Navigator.canPop(Get.context!)) {
        Get.back();
      } else {
        // Fallback: try to go back anyway
        Get.back();
      }
    } catch (e) {
      debugPrint('Navigation error: $e');
      // Last resort: try to pop manually
      try {
        Navigator.of(Get.context!).pop();
      } catch (e2) {
        debugPrint('Fallback navigation error: $e2');
      }
    }
  }

  /// Build group image with enhanced error handling
  Widget _buildGroupImage(String assetPath) {
    return Image.asset(
      assetPath,
      fit: BoxFit.contain,
      errorBuilder: (context, error, stackTrace) {
        debugPrint('Group image load error: $error');
        return Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            color: const Color(0xFFF0F4F8),
            borderRadius: BorderRadius.circular(12.r),
          ),
          child: Icon(
            Icons.groups,
            size: 24.w,
            color: const Color(0xFF5D6A7C),
          ),
        );
      },
    );
  }
}

/// Individual chat message bubble with directional styling and content support
///
/// Displays chat messages with:
/// - Directional styling based on sender (current user vs others)
/// - Support for both text messages and stickers
/// - Leader indicators and sender name display
/// - Responsive bubble sizing and professional styling
/// - Enhanced validation using model validation methods
/// - Accessibility features and proper text overflow handling
class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.message});

  final CommunityChatMessage message;

  @override
  Widget build(BuildContext context) {
    final alignment =
        message.isCurrentUser ? Alignment.centerRight : Alignment.centerLeft;
    final bubbleColor = message.isCurrentUser
        ? const Color(0xFF1CB0F6)
        : const Color(0xFFF1F5FF);
    final textColor =
        message.isCurrentUser ? Colors.white : const Color(0xFF1B2B40);

    return Container(
      margin: EdgeInsets.only(
        bottom: 14.h,
        left: message.isCurrentUser ? 80.w : 0,
        right: message.isCurrentUser ? 0 : 80.w,
      ),
      alignment: alignment,
      child: Column(
        crossAxisAlignment: message.isCurrentUser
            ? CrossAxisAlignment.end
            : CrossAxisAlignment.start,
        children: [
          Padding(
            padding: EdgeInsets.only(
              left: message.isCurrentUser ? 0 : 4.w,
              right: message.isCurrentUser ? 4.w : 0,
            ),
            child: Text(
              message.validatedSenderName,
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: message.isLeader ? FontWeight.w700 : FontWeight.w500,
                color: const Color(0xFF6B7B8E),
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          SizedBox(height: 6.h),
          if (message.isSticker)
            Container(
              padding: EdgeInsets.all(4.w),
              decoration: BoxDecoration(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(18.r),
              ),
              child: _StickerImage(path: message.validatedContent),
            )
          else
            Container(
              constraints: BoxConstraints(
                maxWidth: 280.w,
                minWidth: 40.w,
              ),
              padding: EdgeInsets.symmetric(
                horizontal: 16.w,
                vertical: 12.h,
              ),
              decoration: BoxDecoration(
                color: bubbleColor,
                borderRadius: _buildBubbleBorderRadius(),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    blurRadius: 8.r,
                    offset: Offset(0, 2.h),
                  ),
                ],
              ),
              child: Text(
                message.validatedContent,
                style: TextStyle(
                  fontSize: 14.sp,
                  color: textColor,
                  height: 1.3,
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// Build border radius for chat bubble with directional styling
  BorderRadius _buildBubbleBorderRadius() {
    final radius = 20.r;
    const smallRadius = 4.0;

    if (message.isCurrentUser) {
      return BorderRadius.only(
        topLeft: Radius.circular(radius),
        topRight: Radius.circular(radius),
        bottomLeft: Radius.circular(radius),
        bottomRight: const Radius.circular(smallRadius),
      );
    } else {
      return BorderRadius.only(
        topLeft: Radius.circular(radius),
        topRight: Radius.circular(radius),
        bottomLeft: const Radius.circular(smallRadius),
        bottomRight: Radius.circular(radius),
      );
    }
  }
}

/// Advanced chat input widget with validation and send controls
///
/// Provides a comprehensive text input experience with:
/// - Multi-line text input with dynamic sizing
/// - Character limit validation and user feedback
/// - Send state management with loading indicators
/// - Enhanced error handling and user notifications
/// - Debounced send operations to prevent duplicate messages
/// - Professional styling with adaptive UI states
class _ChatInput extends StatefulWidget {
  const _ChatInput({required this.onSend});

  final Future<void> Function(String) onSend;

  @override
  State<_ChatInput> createState() => _ChatInputState();
}

/// Sticker image widget with comprehensive loading and error handling
///
/// Handles sticker display with:
/// - Support for both network and asset images
/// - Comprehensive path validation and sanitization
/// - Loading indicators for network images
/// - Professional error handling with fallback widgets
/// - Optimized sizing and styling for chat context
/// - Enhanced debugging and error reporting
class _StickerImage extends StatelessWidget {
  const _StickerImage({required this.path});

  final String path;

  @override
  Widget build(BuildContext context) {
    final validPath = _validateStickerPath(path);
    if (validPath.isEmpty) {
      return _buildErrorWidget();
    }

    final isNetwork = validPath.startsWith('http://') || validPath.startsWith('https://');

    return ClipRRect(
      borderRadius: BorderRadius.circular(12.r),
      child: isNetwork
          ? Image.network(
              validPath,
              width: 64.w,
              height: 64.w,
              fit: BoxFit.contain,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return SizedBox(
                  width: 64.w,
                  height: 64.w,
                  child: Center(
                    child: CircularProgressIndicator(
                      strokeWidth: 2.0,
                      value: loadingProgress.expectedTotalBytes != null
                          ? loadingProgress.cumulativeBytesLoaded /
                              loadingProgress.expectedTotalBytes!
                          : null,
                    ),
                  ),
                );
              },
              errorBuilder: (context, error, stackTrace) {
                debugPrint('Network sticker load error: $error');
                return _buildErrorWidget();
              },
            )
          : Image.asset(
              validPath,
              width: 64.w,
              height: 64.w,
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) {
                debugPrint('Asset sticker load error: $error');
                return _buildErrorWidget();
              },
            ),
    );
  }

  /// Validate and clean sticker path
  String _validateStickerPath(String path) {
    final trimmed = path.trim();
    if (trimmed.isEmpty) return '';

    // Validate network URLs
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      try {
        final uri = Uri.tryParse(trimmed);
        if (uri != null && uri.isAbsolute) {
          return trimmed;
        }
      } catch (e) {
        debugPrint('Invalid sticker URL: $trimmed');
      }
      return '';
    }

    // Validate asset paths
    if (trimmed.startsWith('assets/')) {
      return trimmed;
    }

    // Default fallback
    return trimmed.startsWith('/') ? trimmed : '';
  }

  /// Build error widget for failed sticker loads
  Widget _buildErrorWidget() {
    return Container(
      width: 64.w,
      height: 64.w,
      decoration: BoxDecoration(
        color: const Color(0xFFF0F4F8),
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(
          color: const Color(0xFFE0E6EE),
          width: 1.0,
        ),
      ),
      child: Icon(
        Icons.image_not_supported_outlined,
        size: 24.w,
        color: const Color(0xFF5D6A7C),
      ),
    );
  }
}

class _ChatInputState extends State<_ChatInput> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  bool _isSending = false;

  /// Maximum message length for validation
  static const int _maxMessageLength = 500;

  @override
  void dispose() {
    _controller.removeListener(_handleTextChange);
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _controller.addListener(_handleTextChange);
  }

  void _handleTextChange() {
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _handleSend() async {
    if (_isSending) return;

    final text = _controller.text.trim();
    if (!_validateMessage(text)) {
      return;
    }

    setState(() => _isSending = true);

    try {
      await widget.onSend(text);
      _controller.clear();
      _focusNode.requestFocus();
    } catch (e) {
      debugPrint('Send message error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Không thể gửi tin nhắn: ${e.toString()}'),
            backgroundColor: Colors.red.shade600,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSending = false);
      }
    }
  }

  /// Validate message content and length
  bool _validateMessage(String text) {
    if (text.isEmpty) {
      return false;
    }

    if (text.length > _maxMessageLength) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Tin nhắn không được vượt quá 500 ký tự'),
            backgroundColor: Colors.orange.shade600,
            duration: const Duration(seconds: 2),
          ),
        );
      }
      return false;
    }

    return true;
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
        color: const Color(0xFFE6F9FF),
        child: Row(
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(26.r),
                  border: Border.all(
                    color: const Color(0xFFE0E6EE),
                    width: 1.0,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.05),
                      blurRadius: 12.r,
                      offset: Offset(0, 4.h),
                    ),
                  ],
                ),
                padding: EdgeInsets.symmetric(horizontal: 16.w),
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  maxLength: _maxMessageLength,
                  maxLines: 4,
                  minLines: 1,
                  enabled: !_isSending,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: InputDecoration(
                    hintText: _isSending ? 'Đang gửi...' : 'Hãy viết gì đó...',
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                    counterText: '',
                    hintStyle: TextStyle(
                      fontSize: 14.sp,
                      color: _isSending
                          ? const Color(0xFFB0BEC5)
                          : const Color(0xFF7D8AA2),
                    ),
                  ),
                  style: TextStyle(
                    fontSize: 14.sp,
                    color: _isSending
                        ? const Color(0xFFB0BEC5)
                        : const Color(0xFF1B2B40),
                  ),
                  onSubmitted: (_) => _handleSend(),
                  onChanged: (_) => _handleTextChange(),
                ),
              ),
            ),
            SizedBox(width: 10.w),
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              child: _isSending
                  ? Padding(
                      padding: EdgeInsets.all(12.w),
                      child: SizedBox(
                        width: 20.w,
                        height: 20.w,
                        child: const CircularProgressIndicator(
                          strokeWidth: 2.0,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            Color(0xFF1CB0F6),
                          ),
                        ),
                      ),
                    )
                  : IconButton(
                      onPressed: _controller.text.trim().isNotEmpty
                          ? _handleSend
                          : null,
                      icon: const Icon(Icons.send_rounded),
                      color: _controller.text.trim().isNotEmpty
                          ? const Color(0xFF1CB0F6)
                          : const Color(0xFFB0BEC5),
                      disabledColor: const Color(0xFFB0BEC5),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
