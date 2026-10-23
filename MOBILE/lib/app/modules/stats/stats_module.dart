import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/prismo.dart';
import '../../data/models/api/common.dart';
import '../../data/models/api/vocab.dart';
import '../../routes/app_pages.dart';
import '../../core/widgets/show_more.dart';

/// Thống kê học tập (same numbers as the web's /stats): answers by day, by question type,
/// by topic and the words answered wrong most often – for the language being learned.
class StatsView extends StatefulWidget {
  const StatsView({super.key});

  @override
  State<StatsView> createState() => _StatsViewState();
}

class _StatsViewState extends State<StatsView> {
  int _days = 30;
  late Future<Map<String, dynamic>> _future = _load();

  Future<Map<String, dynamic>> _load() async =>
      asMap(await ApiClient.to.get('/stats/learning/', query: {'days': _days}));

  void _setDays(int d) => setState(() {
        _days = d;
        _future = _load();
      });

  String _pct(dynamic v) => v == null ? '–' : '${((v as num) * 100).round()}%';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Thống kê học tập')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snap.hasError || snap.data == null) {
            return Center(child: Text('Không tải được số liệu. Kéo xuống để thử lại.', style: TextStyle(color: AppColors.textSecondary)));
          }
          final s = snap.data!;
          final words = asMap(s['words']);
          final daily = asMapList(s['daily']);
          final maxDay = daily.fold<int>(1, (m, d) => asInt(d['answers']) > m ? asInt(d['answers']) : m);
          final hardest = asMapList(s['hardest']);
          return RefreshIndicator(
            onRefresh: () async => _setDays(_days),
            child: ListView(
              padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 32.h),
              children: [
                SegmentedButton<int>(
                  segments: const [
                    ButtonSegment(value: 7, label: Text('7 ngày')),
                    ButtonSegment(value: 30, label: Text('30 ngày')),
                    ButtonSegment(value: 90, label: Text('90 ngày')),
                  ],
                  selected: {_days},
                  onSelectionChanged: (v) => _setDays(v.first),
                  showSelectedIcon: false,
                ),
                SizedBox(height: 16.h),
                if (asInt(s['answers']) == 0 && asInt(words['total']) == 0)
                  _Card(
                    child: Column(children: [
                      Prismo(mood: PrismoMood.wow, size: 90.w),
                      SizedBox(height: 8.h),
                      Text('Chưa có số liệu', style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                      SizedBox(height: 4.h),
                      Text('Học vài từ mới, số liệu của bạn sẽ hiện ở đây.', textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
                    ]),
                  )
                else ...[
                  _Card(
                    child: Wrap(spacing: 24.w, runSpacing: 14.h, children: [
                      _Fact('${asInt(words['total'])}', 'từ trong thư viện'),
                      _Fact('${asInt(words['mastered'])}', 'từ đã thuộc'),
                      _Fact('${asInt(s['answers'])}', 'câu trả lời'),
                      _Fact(_pct(s['accuracy']), 'trả lời đúng'),
                      _Fact(_pct(s['first_try_accuracy']), 'đúng lần đầu'),
                      _Fact('${asInt(s['active_days'])}/$_days', 'ngày có học'),
                    ]),
                  ),
                  SizedBox(height: 12.h),
                  _Card(
                    title: 'Câu trả lời mỗi ngày',
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        _Legend(AppColors.beamMint, 'Đúng'),
                        SizedBox(width: 14.w),
                        _Legend(AppColors.beamCoral, 'Sai'),
                      ]),
                      SizedBox(height: 10.h),
                      SizedBox(
                        height: 120.h,
                        child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
                          for (final d in daily)
                            Expanded(
                              child: Padding(
                                padding: EdgeInsets.symmetric(horizontal: daily.length > 40 ? 0.5 : 1.5),
                                child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
                                  Container(height: 120.h * (asInt(d['answers']) - asInt(d['correct'])) / maxDay, color: AppColors.beamCoral),
                                  Container(height: 120.h * asInt(d['correct']) / maxDay, color: AppColors.beamMint),
                                ]),
                              ),
                            ),
                        ]),
                      ),
                    ]),
                  ),
                  SizedBox(height: 12.h),
                  _Card(
                    title: 'Theo dạng câu hỏi',
                    child: Column(children: [
                      for (final r in asMapList(s['by_question_type']))
                        _MeterRow(label: asString(r['label']), right: '${asInt(r['answers'])} câu', value: r['accuracy'] as num?, pct: _pct(r['accuracy'])),
                    ]),
                  ),
                  SizedBox(height: 12.h),
                  _Card(
                    title: 'Theo chủ đề',
                    child: ShowMoreColumn(limit: 6, label: 'Xem tất cả chủ đề', children: [
                      for (final t in asMapList(s['by_topic']))
                        _MeterRow(
                          label: '${asString(t['icon'])} ${asString(t['name'])}',
                          right: 'thuộc ${asInt(t['mastered'])}/${asInt(t['words'])}',
                          value: asInt(t['words']) == 0 ? 0 : asInt(t['mastered']) / asInt(t['words']),
                          pct: _pct(t['accuracy']),
                          color: AppColors.beamMint,
                        ),
                    ]),
                  ),
                  if (hardest.isNotEmpty) ...[
                    SizedBox(height: 12.h),
                    _Card(
                      title: 'Từ hay sai',
                      child: Column(children: [
                        ShowMoreColumn(limit: 8, label: 'Xem tất cả từ hay sai', children: [
                        for (final h in hardest)
                          Builder(builder: (context) {
                            final c = WordCard.fromJson(asMap(h['card']));
                            return ListTile(
                              contentPadding: EdgeInsets.zero,
                              title: Text(c.text, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                              subtitle: Text(c.meaningVi, style: TextStyle(color: AppColors.textSecondary)),
                              trailing: Text('sai ${asInt(h['wrong'])}/${asInt(h['answers'])}',
                                  style: TextStyle(color: AppColors.error, fontWeight: FontWeight.w700)),
                            );
                          }),
                        ]),
                        SizedBox(height: 8.h),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton(onPressed: () => Get.toNamed(Routes.home), child: const Text('Về trang chủ để ôn tập')),
                        ),
                      ]),
                    ),
                  ],
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child, this.title});
  final Widget child;
  final String? title;

  @override
  Widget build(BuildContext context) => Container(
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.fromBorderSide(BorderSide(color: AppColors.line)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          if (title != null) ...[
            Text(title!, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
            SizedBox(height: 12.h),
          ],
          child,
        ]),
      );
}

class _Fact extends StatelessWidget {
  const _Fact(this.value, this.label);
  final String value, label;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text(value,
            style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary,
                fontFeatures: const [FontFeature.tabularFigures()])),
        Text(label, style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
      ]);
}

class _Legend extends StatelessWidget {
  const _Legend(this.color, this.label);
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 10.w, height: 10.w, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(2))),
        SizedBox(width: 6.w),
        Text(label, style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
      ]);
}

class _MeterRow extends StatelessWidget {
  const _MeterRow({required this.label, required this.right, required this.value, required this.pct, this.color});
  final String label, right, pct;
  final num? value;
  final Color? color;

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(bottom: 12.h),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text(label, style: TextStyle(fontWeight: FontWeight.w600, color: AppColors.textPrimary))),
            Text(right, style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
          ]),
          SizedBox(height: 6.h),
          Row(children: [
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(6.r),
                child: LinearProgressIndicator(
                  value: (value ?? 0).toDouble().clamp(0, 1),
                  minHeight: 8.h,
                  color: color ?? AppColors.primary,
                  backgroundColor: AppColors.surfaceMuted,
                ),
              ),
            ),
            SizedBox(width: 10.w),
            SizedBox(width: 40.w, child: Text(pct, textAlign: TextAlign.right, style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textPrimary))),
          ]),
        ]),
      );
}
