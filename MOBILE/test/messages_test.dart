import 'package:flutter_test/flutter_test.dart';
import 'package:lingoprism/app/modules/messages/messages_module.dart';

void main() {
  test('a conversation and its last message are read from the server JSON', () {
    final t = DirectThread.fromJson({
      'id': 3,
      'other': {'id': 19, 'display_name': 'Hải Yến', 'avatar': null},
      'unread': 2,
      'can_message': true,
      'last_message': {'id': 7, 'thread': 3, 'sender': 19, 'content': '你好', 'client_id': '', 'read_at': null,
          'created_at': '2026-10-22T10:00:00+00:00'},
    });
    expect(t.other.displayName, 'Hải Yến');
    expect(t.unread, 2);
    expect(t.last!.content, '你好');
    expect(t.last!.readAt, isNull);
    expect(t.last!.seen().readAt, isNotNull);
  });

  test('a thread the two can no longer write in', () {
    final t = DirectThread.fromJson({'id': 1, 'other': {'id': 2}, 'can_message': false, 'last_message': null});
    expect(t.canMessage, isFalse);
    expect(t.last, isNull);
  });
}
