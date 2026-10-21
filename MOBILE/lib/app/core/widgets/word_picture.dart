import 'package:flutter/material.dart';

/// Real photo of a word (Wikimedia Commons); the emoji only when there is no photo or it fails to load.
class WordPicture extends StatelessWidget {
  const WordPicture({super.key, this.imageUrl, this.emoji = '', required this.size});

  final String? imageUrl;
  final String emoji;
  final double size;

  @override
  Widget build(BuildContext context) {
    final fallback = emoji.isEmpty
        ? SizedBox(width: size, height: size)
        : SizedBox(
            width: size,
            height: size,
            child: Center(child: Text(emoji, style: TextStyle(fontSize: size * 0.6))),
          );
    final url = imageUrl ?? '';
    if (url.isEmpty) return fallback;
    return ClipRRect(
      borderRadius: BorderRadius.circular(size * 0.08),
      child: Image.network(
        url,
        width: size,
        height: size,
        fit: size > 100 ? BoxFit.contain : BoxFit.cover,
        errorBuilder: (_, __, ___) => fallback,
        loadingBuilder: (_, child, progress) => progress == null
            ? child
            : SizedBox(width: size, height: size, child: const Center(child: CircularProgressIndicator(strokeWidth: 2))),
      ),
    );
  }
}
