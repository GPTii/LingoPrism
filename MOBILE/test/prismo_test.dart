import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lingoprism/app/core/widgets/prism_effects.dart';
import 'package:lingoprism/app/core/widgets/prismo.dart';

Widget _host(Widget child) => ScreenUtilInit(
      designSize: const Size(375, 812),
      builder: (_, __) => MaterialApp(home: Scaffold(body: Center(child: child))),
    );

void main() {
  testWidgets('Prismo paints every mood and reacts to a mood change', (tester) async {
    for (final mood in PrismoMood.values) {
      await tester.pumpWidget(_host(Prismo(mood: mood, size: 120, blink: false)));
      await tester.pump(const Duration(milliseconds: 700));
      expect(find.byType(Prismo), findsOneWidget);
      expect(tester.takeException(), isNull);
    }
  });

  testWidgets('PrismBurst plays once and ends empty', (tester) async {
    await tester.pumpWidget(_host(const PrismBurst(child: SizedBox(width: 120, height: 120))));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pump(const Duration(milliseconds: 1400));
    expect(tester.takeException(), isNull);
  });

  testWidgets('PrismoReaction shows and goes away by itself', (tester) async {
    await tester.pumpWidget(_host(Builder(
      builder: (context) => TextButton(onPressed: () => PrismoReaction.show(context, correct: true), child: const Text('go')),
    )));
    await tester.tap(find.text('go'));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('Đúng rồi!'), findsOneWidget);
    await tester.pump(const Duration(milliseconds: 1500));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('Đúng rồi!'), findsNothing);
  });
}
