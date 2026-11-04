import 'dart:convert';

import 'package:dio/dio.dart' show FormData, MultipartFile;
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart' hide FormData, MultipartFile;
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../data/models/api/common.dart';
import '../../data/repositories/repositories.dart';

/// Assignments of a study group (same as the web tab "Bài tập", server: apps.classwork, /assignments/).
/// No teacher role: the group's leaders give and mark the work, the other members do it.

const _kinds = {'mcq': 'Trắc nghiệm', 'fill': 'Điền từ', 'essay': 'Tự luận', 'file': 'Nộp file'};
const _fileTypes = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'webp', 'heic',
    'mp3', 'm4a', 'wav', 'zip'];

num? _num(dynamic v) => v == null || v == '' ? null : num.tryParse('$v');
String _fmt(dynamic v) {
  final n = _num(v);
  if (n == null) return '–';
  return n == n.roundToDouble() ? n.toInt().toString() : n.toStringAsFixed(2).replaceFirst(RegExp(r'0+$'), '');
}

String _when(dynamic iso) {
  final d = DateTime.tryParse('${iso ?? ''}');
  return d == null ? '' : DateFormat('HH:mm dd/MM/yyyy').format(d.toLocal());
}

void _toast(String title, [String body = '']) => Get.snackbar(title, body, snackPosition: SnackPosition.BOTTOM);
void _fail(Object e) => _toast('Không thực hiện được', ApiClient.toApiException(e).message);

Future<void> _openUrl(String? url) async {
  if (url != null && url.isNotEmpty) await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
}

Future<PlatformFile?> _pick({List<String> types = _fileTypes}) async {
  final r = await FilePicker.pickFiles(type: FileType.custom, allowedExtensions: types);
  final f = r?.files.single;
  if (f?.path == null) return null;
  if (f!.size > 10 * 1024 * 1024) {
    _toast('File quá lớn', 'Tối đa 10 MB');
    return null;
  }
  return f;
}

Future<MultipartFile> _part(PlatformFile f) => MultipartFile.fromFile(f.path!, filename: f.name);

class ClassworkApi {
  static ApiClient get _api => ApiClient.to;

  static Future<List<Map<String, dynamic>>> list(int group) async =>
      asMapList(await _api.get('/assignments/', query: {'group': group}));
  static Future<Map<String, dynamic>> get(int id) async => asMap(await _api.get('/assignments/$id/'));
  static Future<Map<String, dynamic>> create(Map<String, dynamic> d) async => asMap(await _api.post('/assignments/', data: d));
  static Future<Map<String, dynamic>> update(int id, Map<String, dynamic> d) async =>
      asMap(await _api.patch('/assignments/$id/', data: d));
  static Future<void> remove(int id) => _api.delete('/assignments/$id/');
  static Future<Map<String, dynamic>> attach(int id, PlatformFile f) async =>
      asMap(await _api.post('/assignments/$id/attachment/', data: FormData.fromMap({'file': await _part(f)})));
  static Future<Map<String, dynamic>> detach(int id) async => asMap(await _api.delete('/assignments/$id/attachment/'));
  static Future<Map<String, dynamic>> action(int id, String what) async =>
      asMap(await _api.post('/assignments/$id/$what/'));
  static Future<Map<String, dynamic>> importFile(int group, PlatformFile f) async => asMap(await _api.post(
      '/assignments/import/', data: FormData.fromMap({'group': '$group', 'file': await _part(f)})));
  static Future<Map<String, dynamic>> submit(int id, List<Map<String, dynamic>> answers, Map<String, PlatformFile> files,
      String text) async {
    final form = FormData.fromMap({'answers': jsonEncode(answers), 'text': text});
    for (final e in files.entries) {
      form.files.add(MapEntry(e.key, await _part(e.value)));
    }
    return asMap(await _api.post('/assignments/$id/submit/', data: form));
  }

  static Future<List<Map<String, dynamic>>> submissions(int id) async =>
      asMapList(await _api.get('/assignments/$id/submissions/'));
  static Future<Map<String, dynamic>> submission(int id, int sid) async =>
      asMap(await _api.get('/assignments/$id/submissions/$sid/'));
  static Future<Map<String, dynamic>> grade(int id, int sid, Map<String, dynamic> d) async =>
      asMap(await _api.post('/assignments/$id/submissions/$sid/grade/', data: d));
}

Widget _chip(String text, Color color) => Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8.r)),
      child: Text(text, style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w700, color: color)),
    );

Widget _status(Map a) {
  final mine = a['my_submission'] as Map?;
  if (a['status'] == 'draft') return _chip('Bản nháp', AppColors.textSecondary);
  if (a['status'] == 'closed') return _chip('Đã đóng', AppColors.textSecondary);
  if (a['is_leader'] == true) return _chip('Đã giao', AppColors.primary);
  if (mine == null) {
    final due = DateTime.tryParse('${a['due_at'] ?? ''}');
    return due != null && due.isBefore(DateTime.now()) ? _chip('Quá hạn', AppColors.error) : _chip('Chưa làm', AppColors.beamAmber);
  }
  return mine['status'] == 'graded'
      ? _chip('Đã chấm ${_fmt(mine['score'])}/${_fmt(mine['max_score'])}', AppColors.success)
      : _chip('Đã nộp', AppColors.primary);
}

BoxDecoration _card() => BoxDecoration(
    color: AppColors.surface, borderRadius: BorderRadius.circular(14.r), border: Border.all(color: AppColors.line));

// ---------------------------------------------------------------- list

class AssignmentListView extends StatefulWidget {
  const AssignmentListView({super.key, required this.groupId, required this.groupName});

  final int groupId;
  final String groupName;

  @override
  State<AssignmentListView> createState() => _AssignmentListViewState();
}

class _AssignmentListViewState extends State<AssignmentListView> {
  late Future<(bool, List<Map<String, dynamic>>)> _data = _load();

  Future<(bool, List<Map<String, dynamic>>)> _load() async {
    final group = await CommunityRepository.group(widget.groupId);
    return (group.isLeader, await ClassworkApi.list(widget.groupId));
  }

  void _reload() => setState(() => _data = _load());

  Future<void> _open(int id) async {
    await Get.to(() => AssignmentDetailView(id: id));
    _reload();
  }

  Future<void> _addMember() async {
    final input = TextEditingController();
    final ok = await Get.dialog<bool>(AlertDialog(
      title: const Text('Thêm thành viên'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        const Text('Nhập ID 8 số của người muốn thêm (xem trong Hồ sơ). Bạn bè được thêm ngay, người khác nhận lời mời.'),
        SizedBox(height: 10.h),
        TextField(controller: input, keyboardType: TextInputType.number, maxLength: 8, decoration: const InputDecoration(hintText: '12345678')),
      ]),
      actions: [
        TextButton(onPressed: () => Get.back(result: false), child: const Text('Huỷ')),
        FilledButton(onPressed: () => Get.back(result: true), child: const Text('Thêm')),
      ],
    ));
    if (ok != true || input.text.trim().length != 8) return;
    try {
      final m = await CommunityRepository.addMember(widget.groupId, input.text.trim());
      final name = asMap(m['user'])['display_name'] ?? '';
      _toast(m['status'] == 'active' ? 'Đã thêm $name vào nhóm' : 'Đã gửi lời mời tới $name');
    } catch (e) {
      _fail(e);
    }
  }

  Future<void> _create() async {
    final title = TextEditingController();
    final choice = await Get.bottomSheet<String>(
      Container(
        padding: EdgeInsets.fromLTRB(16.w, 16.h, 16.w, 24.h),
        decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.vertical(top: Radius.circular(20.r))),
        child: SafeArea(
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('Tạo bài tập', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800)),
            SizedBox(height: 12.h),
            TextField(controller: title, decoration: const InputDecoration(labelText: 'Tên bài tập', hintText: 'VD: Bài 3 – Gia đình')),
            SizedBox(height: 14.h),
            OutlinedButton.icon(onPressed: () => Get.back(result: 'blank'), icon: const Icon(Icons.edit_note_rounded),
                label: const Text('Tự soạn câu hỏi')),
            SizedBox(height: 8.h),
            FilledButton.icon(onPressed: () => Get.back(result: 'ai'), icon: const Icon(Icons.auto_awesome_rounded),
                label: const Text('Tải file đề – AI tách thành câu hỏi')),
            SizedBox(height: 8.h),
            Text('PDF, Word (.docx), ảnh chụp phiếu bài tập hoặc .txt. Câu hỏi AI tách ra là bản nháp: kiểm tra, sửa đáp án rồi mới giao.',
                style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
          ]),
        ),
      ),
      isScrollControlled: true,
    );
    if (choice == null) return;
    PlatformFile? file;
    Map<String, dynamic>? draft;
    if (choice == 'ai') {
      file = await _pick(types: ['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'webp']);
      if (file == null) return;
      Get.dialog(const Center(child: CircularProgressIndicator()), barrierDismissible: false);
      try {
        draft = await ClassworkApi.importFile(widget.groupId, file);
      } catch (e) {
        Get.back();
        _fail(e);
        return;
      }
      Get.back();
    }
    try {
      final name = title.text.trim().isNotEmpty ? title.text.trim()
          : (draft?['title'] as String?)?.isNotEmpty == true ? draft!['title'] as String
          : file?.name.replaceAll(RegExp(r'\.[^.]+$'), '') ?? 'Bài tập mới';
      final a = await ClassworkApi.create({'group': widget.groupId, 'title': name, 'questions': draft?['questions'] ?? [],
          'ai_generated': draft != null});
      if (file != null && RegExp(r'\.(pdf|docx?|jpe?g|png|webp)$', caseSensitive: false).hasMatch(file.name)) {
        await ClassworkApi.attach(asInt(a['id']), file).catchError((_) => <String, dynamic>{});
      }
      await _open(asInt(a['id']));
    } catch (e) {
      _fail(e);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<(bool, List<Map<String, dynamic>>)>(
      future: _data,
      builder: (context, snap) {
        final leader = snap.data?.$1 == true;
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(title: Text('Bài tập · ${widget.groupName}', overflow: TextOverflow.ellipsis), actions: [
            if (leader) IconButton(tooltip: 'Thêm thành viên', onPressed: _addMember, icon: const Icon(Icons.person_add_alt_1_rounded)),
          ]),
          floatingActionButton: leader
              ? FloatingActionButton.extended(onPressed: _create, icon: const Icon(Icons.add), label: const Text('Tạo bài tập'))
              : null,
          body: snap.connectionState != ConnectionState.done
              ? const Center(child: CircularProgressIndicator())
              : snap.hasError
                  ? Center(child: Text(ApiClient.toApiException(snap.error!).message))
                  : RefreshIndicator(
                      onRefresh: () async => _reload(),
                      child: snap.data!.$2.isEmpty
                          ? ListView(children: [
                              SizedBox(height: 120.h),
                              Center(child: Text(leader ? 'Chưa có bài tập. Bấm "Tạo bài tập" để giao bài.' : 'Trưởng nhóm chưa giao bài nào.',
                                  style: TextStyle(color: AppColors.textSecondary))),
                            ])
                          : ListView(padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 96.h), children: [
                              for (final a in snap.data!.$2)
                                Padding(
                                  padding: EdgeInsets.only(bottom: 10.h),
                                  child: InkWell(
                                    borderRadius: BorderRadius.circular(14.r),
                                    onTap: () => _open(asInt(a['id'])),
                                    child: Container(
                                      padding: EdgeInsets.all(14.w),
                                      decoration: _card(),
                                      child: Row(children: [
                                        Icon(Icons.assignment_rounded, color: AppColors.primary, size: 26.sp),
                                        SizedBox(width: 10.w),
                                        Expanded(
                                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                            Text('${a['title']}', style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700)),
                                            Text(
                                              [
                                                asInt(a['question_count']) > 0 ? '${a['question_count']} câu' : 'Nộp bài làm / file',
                                                '${_fmt(a['max_score'])} điểm',
                                                if (a['due_at'] != null) 'hạn ${_when(a['due_at'])}',
                                                if (a['is_leader'] == true && a['counts'] != null && a['status'] != 'draft')
                                                  'nộp ${a['counts']['submitted']}/${a['counts']['members']}',
                                              ].join(' · '),
                                              style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary),
                                            ),
                                          ]),
                                        ),
                                        _status(a),
                                      ]),
                                    ),
                                  ),
                                ),
                            ]),
                    ),
        );
      },
    );
  }
}

// ---------------------------------------------------------------- one assignment

class AssignmentDetailView extends StatefulWidget {
  const AssignmentDetailView({super.key, required this.id});

  final int id;

  @override
  State<AssignmentDetailView> createState() => _AssignmentDetailViewState();
}

class _AssignmentDetailViewState extends State<AssignmentDetailView> {
  late Future<Map<String, dynamic>> _a = ClassworkApi.get(widget.id);
  bool _editing = false;

  void _set(Map<String, dynamic> a) => setState(() => _a = Future.value(a));
  void _reload() => setState(() => _a = ClassworkApi.get(widget.id));

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _a,
      builder: (context, snap) {
        final a = snap.data;
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(title: Text(a == null ? 'Bài tập' : '${a['title']}', overflow: TextOverflow.ellipsis)),
          body: snap.connectionState != ConnectionState.done
              ? const Center(child: CircularProgressIndicator())
              : snap.hasError
                  ? Center(child: Text(ApiClient.toApiException(snap.error!).message))
                  : a!['is_leader'] == true && (a['status'] == 'draft' || _editing)
                      ? _Editor(a: a, onSaved: (x, {bool done = false}) {
                          if (done) _editing = false;
                          _set(x);
                        })
                      : a['is_leader'] == true
                          ? _LeaderPanel(a: a, onChanged: _set, onEdit: () => setState(() => _editing = true), onReload: _reload)
                          : _DoPanel(a: a, onChanged: _set),
        );
      },
    );
  }
}

Widget _header(Map a) {
  return Container(
    padding: EdgeInsets.all(14.w),
    decoration: _card(),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Expanded(child: Text('${a['title']}', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800))),
        _status(a),
      ]),
      SizedBox(height: 4.h),
      Text(
        [
          asInt(a['question_count']) > 0 ? '${a['question_count']} câu' : 'Nộp bài làm / file',
          '${_fmt(a['max_score'])} điểm',
          if (a['due_at'] != null) 'hạn ${_when(a['due_at'])}${a['allow_late'] == false ? ' (không nhận muộn)' : ''}',
        ].join(' · '),
        style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary),
      ),
      if ('${a['instructions'] ?? ''}'.isNotEmpty) ...[SizedBox(height: 8.h), Text('${a['instructions']}')],
      if (a['attachment'] != null)
        TextButton.icon(onPressed: () => _openUrl(a['attachment'] as String?), icon: const Icon(Icons.attach_file_rounded),
            label: Text('${a['attachment_name']}', overflow: TextOverflow.ellipsis)),
    ]),
  );
}

// ---------------------------------------------------------------- leader: editor

class _Editor extends StatefulWidget {
  const _Editor({required this.a, required this.onSaved});

  final Map<String, dynamic> a;
  final void Function(Map<String, dynamic> a, {bool done}) onSaved;

  @override
  State<_Editor> createState() => _EditorState();
}

class _EditorState extends State<_Editor> {
  late final Map<String, dynamic> a = widget.a;
  late final title = TextEditingController(text: '${a['title']}');
  late final instructions = TextEditingController(text: '${a['instructions'] ?? ''}');
  late DateTime? due = DateTime.tryParse('${a['due_at'] ?? ''}')?.toLocal();
  late num points = _num(a['points']) ?? 10;
  late bool allowLate = a['allow_late'] != false;
  late bool showAnswers = a['show_answers'] != false;
  late bool ai = a['ai_generated'] == true;
  late final List<Map<String, dynamic>> questions =
      asMapList(a['questions']).map((q) => {...q, 'options': asMapList(q['options']).map((o) => {...o}).toList()}).toList();
  String busy = '';

  bool get locked => a['status'] != 'draft' && asInt((a['counts'] as Map?)?['submitted']) > 0;

  Map<String, dynamic> _blank(String kind) => {
        'kind': kind, 'prompt': '', 'points': 1, 'explanation': '', 'accepted_answers': <String>[],
        'options': kind == 'mcq' ? [{'text': '', 'correct': true}, {'text': '', 'correct': false}] : [],
      };

  Future<void> _save({bool publish = false}) async {
    setState(() => busy = publish ? 'publish' : 'save');
    try {
      var x = await ClassworkApi.update(asInt(a['id']), {
        'title': title.text.trim(), 'instructions': instructions.text, 'due_at': due?.toUtc().toIso8601String(),
        'points': points, 'allow_late': allowLate, 'show_answers': showAnswers, 'ai_generated': ai,
        if (!locked) 'questions': questions,
      });
      if (publish) x = await ClassworkApi.action(asInt(a['id']), 'publish');
      _toast(publish ? 'Đã giao bài cho cả nhóm' : 'Đã lưu');
      widget.onSaved(x, done: publish || a['status'] != 'draft');
    } catch (e) {
      _fail(e);
    } finally {
      if (mounted) setState(() => busy = '');
    }
  }

  Future<void> _importAi() async {
    final f = await _pick(types: ['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'webp']);
    if (f == null) return;
    setState(() => busy = 'ai');
    try {
      final d = await ClassworkApi.importFile(asInt(a['group']), f);
      setState(() {
        questions.addAll(asMapList(d['questions']));
        ai = true;
      });
      _toast('AI tách được ${asMapList(d['questions']).length} câu', 'Hãy kiểm tra lại nội dung và đáp án');
    } catch (e) {
      _fail(e);
    } finally {
      if (mounted) setState(() => busy = '');
    }
  }

  Future<void> _pickDue() async {
    final now = DateTime.now();
    final d = await showDatePicker(context: context, initialDate: due ?? now, firstDate: now.subtract(const Duration(days: 1)),
        lastDate: now.add(const Duration(days: 365)));
    if (d == null || !mounted) return;
    final t = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(due ?? DateTime(d.year, d.month, d.day, 21)));
    setState(() => due = DateTime(d.year, d.month, d.day, t?.hour ?? 21, t?.minute ?? 0));
  }

  Widget _question(int i) {
    final q = questions[i];
    final options = (q['options'] as List).cast<Map<String, dynamic>>();
    return Container(
      key: ObjectKey(q),
      margin: EdgeInsets.only(bottom: 10.h),
      padding: EdgeInsets.all(12.w),
      decoration: _card(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text('Câu ${i + 1}', style: const TextStyle(fontWeight: FontWeight.w800)),
          SizedBox(width: 8.w),
          DropdownButton<String>(
            value: '${q['kind']}',
            isDense: true,
            items: [for (final e in _kinds.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
            onChanged: locked ? null : (k) => setState(() => questions[i] = {..._blank(k!), 'prompt': q['prompt'], 'points': q['points']}),
          ),
          const Spacer(),
          SizedBox(
            width: 56.w,
            child: TextFormField(
              initialValue: _fmt(q['points']),
              enabled: !locked,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(isDense: true, suffixText: 'đ'),
              onChanged: (v) => q['points'] = num.tryParse(v.replaceAll(',', '.')) ?? 1,
            ),
          ),
          if (!locked)
            IconButton(onPressed: () => setState(() => questions.removeAt(i)), icon: Icon(Icons.delete_outline, color: AppColors.error)),
        ]),
        TextFormField(
          initialValue: '${q['prompt']}',
          enabled: !locked,
          minLines: 1,
          maxLines: 5,
          decoration: const InputDecoration(hintText: 'Nội dung câu hỏi'),
          onChanged: (v) => q['prompt'] = v,
        ),
        if (q['kind'] == 'mcq') ...[
          for (var j = 0; j < options.length; j++)
            Row(key: ObjectKey(options[j]), children: [
              Radio<int>(
                value: j,
                groupValue: options.indexWhere((o) => o['correct'] == true),
                onChanged: locked ? null : (v) => setState(() {
                  for (var k = 0; k < options.length; k++) {
                    options[k]['correct'] = k == v;
                  }
                }),
              ),
              Expanded(
                child: TextFormField(
                  initialValue: '${options[j]['text']}',
                  enabled: !locked,
                  decoration: InputDecoration(isDense: true, hintText: 'Phương án ${String.fromCharCode(65 + j)}'),
                  onChanged: (v) => options[j]['text'] = v,
                ),
              ),
              if (!locked && options.length > 2)
                IconButton(onPressed: () => setState(() => options.removeAt(j)), icon: const Icon(Icons.close, size: 18)),
            ]),
          if (!locked && options.length < 8)
            TextButton.icon(onPressed: () => setState(() => options.add({'text': '', 'correct': false})),
                icon: const Icon(Icons.add), label: const Text('Thêm phương án')),
          Text('Chạm vòng tròn để chọn đáp án đúng', style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary)),
        ],
        if (q['kind'] == 'fill')
          TextFormField(
            initialValue: (q['accepted_answers'] as List? ?? []).join('; '),
            enabled: !locked,
            decoration: const InputDecoration(labelText: 'Đáp án đúng', hintText: 'Nhiều đáp án cách nhau bằng dấu ;'),
            onChanged: (v) => q['accepted_answers'] = v.split(';').map((x) => x.trim()).where((x) => x.isNotEmpty).toList(),
          ),
        if (q['kind'] == 'essay' || q['kind'] == 'file')
          Padding(
            padding: EdgeInsets.only(top: 6.h),
            child: Text(q['kind'] == 'essay' ? 'Học viên viết câu trả lời, bạn chấm tay.' : 'Học viên nộp file (ảnh bài làm, ghi âm…), bạn chấm tay.',
                style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
          ),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final total = questions.fold<num>(0, (s, q) => s + (_num(q['points']) ?? 0));
    return Column(children: [
      Expanded(
        child: ListView(padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 24.h), children: [
          TextField(controller: title, decoration: const InputDecoration(labelText: 'Tên bài tập')),
          TextField(controller: instructions, minLines: 2, maxLines: 6,
              decoration: const InputDecoration(labelText: 'Đề bài / hướng dẫn', hintText: 'VD: Đọc file đính kèm rồi làm bài 1–3')),
          SizedBox(height: 8.h),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.event_rounded),
            title: Text(due == null ? 'Không có hạn nộp' : 'Hạn nộp ${DateFormat('HH:mm dd/MM/yyyy').format(due!)}'),
            trailing: due == null ? null : IconButton(onPressed: () => setState(() => due = null), icon: const Icon(Icons.close)),
            onTap: _pickDue,
          ),
          SwitchListTile(contentPadding: EdgeInsets.zero, value: allowLate, onChanged: (v) => setState(() => allowLate = v),
              title: const Text('Cho nộp muộn')),
          SwitchListTile(contentPadding: EdgeInsets.zero, value: showAnswers, onChanged: (v) => setState(() => showAnswers = v),
              title: const Text('Cho xem đáp án sau khi chấm')),
          if (questions.isEmpty)
            TextFormField(initialValue: _fmt(points), keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Điểm tối đa (bài nộp bài làm / file)'),
                onChanged: (v) => points = num.tryParse(v) ?? 10),
          SizedBox(height: 8.h),
          Wrap(spacing: 8.w, runSpacing: 8.h, children: [
            if (a['attachment'] != null) ...[
              ActionChip(avatar: const Icon(Icons.attach_file, size: 18), label: Text('${a['attachment_name']}'),
                  onPressed: () => _openUrl(a['attachment'] as String?)),
              ActionChip(label: const Text('Bỏ file'), onPressed: () async {
                try {
                  widget.onSaved(await ClassworkApi.detach(asInt(a['id'])));
                } catch (e) {
                  _fail(e);
                }
              }),
            ] else
              ActionChip(avatar: const Icon(Icons.attach_file, size: 18), label: const Text('Đính kèm file đề'), onPressed: () async {
                final f = await _pick();
                if (f == null) return;
                try {
                  widget.onSaved(await ClassworkApi.attach(asInt(a['id']), f));
                } catch (e) {
                  _fail(e);
                }
              }),
            if (!locked)
              ActionChip(
                avatar: busy == 'ai' ? SizedBox(width: 16.w, height: 16.w, child: const CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.auto_awesome_rounded, size: 18),
                label: Text(busy == 'ai' ? 'AI đang đọc đề…' : 'Thêm câu hỏi từ file (AI)'),
                onPressed: busy.isEmpty ? _importAi : null,
              ),
          ]),
          if (ai && !locked)
            Padding(
              padding: EdgeInsets.only(top: 10.h),
              child: const Text('Câu hỏi do AI tách từ file – kiểm tra nội dung và đáp án đúng trước khi giao.',
                  style: TextStyle(color: AppColors.beamAmber, fontWeight: FontWeight.w600)),
            ),
          if (locked)
            Padding(
              padding: EdgeInsets.only(top: 10.h),
              child: Text('Đã có người nộp bài: chỉ sửa được tên, hướng dẫn, hạn nộp và file.',
                  style: TextStyle(color: AppColors.textSecondary)),
            ),
          SizedBox(height: 12.h),
          for (var i = 0; i < questions.length; i++) _question(i),
          if (!locked)
            Wrap(spacing: 8.w, children: [
              for (final e in _kinds.entries)
                OutlinedButton.icon(onPressed: () => setState(() => questions.add(_blank(e.key))), icon: const Icon(Icons.add, size: 18),
                    label: Text(e.value)),
            ]),
        ]),
      ),
      SafeArea(
        top: false,
        child: Container(
          padding: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 8.h),
          decoration: BoxDecoration(color: AppColors.surface, border: Border(top: BorderSide(color: AppColors.line))),
          child: Row(children: [
            Expanded(
              child: Text(questions.isEmpty ? 'Không có câu hỏi · ${_fmt(points)} đ' : '${questions.length} câu · ${_fmt(total)} đ',
                  style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp)),
            ),
            OutlinedButton(onPressed: busy.isEmpty ? () => _save() : null, child: Text(busy == 'save' ? 'Đang lưu…' : 'Lưu')),
            if (a['status'] == 'draft') ...[
              SizedBox(width: 8.w),
              FilledButton.icon(
                onPressed: busy.isEmpty
                    ? () async {
                        final ok = await Get.dialog<bool>(AlertDialog(
                          title: const Text('Giao bài cho cả nhóm?'),
                          content: const Text('Mọi thành viên nhận thông báo và bắt đầu làm được.'),
                          actions: [
                            TextButton(onPressed: () => Get.back(result: false), child: const Text('Chưa')),
                            FilledButton(onPressed: () => Get.back(result: true), child: const Text('Giao bài')),
                          ],
                        ));
                        if (ok == true) _save(publish: true);
                      }
                    : null,
                icon: const Icon(Icons.send_rounded, size: 18),
                label: const Text('Giao bài'),
              ),
            ],
          ]),
        ),
      ),
    ]);
  }
}

// ---------------------------------------------------------------- leader: hand-ins

class _LeaderPanel extends StatefulWidget {
  const _LeaderPanel({required this.a, required this.onChanged, required this.onEdit, required this.onReload});

  final Map<String, dynamic> a;
  final ValueChanged<Map<String, dynamic>> onChanged;
  final VoidCallback onEdit;
  final VoidCallback onReload;

  @override
  State<_LeaderPanel> createState() => _LeaderPanelState();
}

class _LeaderPanelState extends State<_LeaderPanel> {
  late Future<List<Map<String, dynamic>>> _rows = ClassworkApi.submissions(asInt(widget.a['id']));

  Future<void> _act(String what) async {
    try {
      widget.onChanged(await ClassworkApi.action(asInt(widget.a['id']), what));
    } catch (e) {
      _fail(e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final a = widget.a;
    return ListView(padding: EdgeInsets.all(16.w), children: [
      _header(a),
      SizedBox(height: 8.h),
      Wrap(spacing: 8.w, children: [
        OutlinedButton(onPressed: widget.onEdit, child: const Text('Sửa')),
        OutlinedButton(onPressed: () => _act(a['status'] == 'published' ? 'close' : 'reopen'),
            child: Text(a['status'] == 'published' ? 'Đóng nộp bài' : 'Mở lại')),
        TextButton(
          onPressed: () async {
            final ok = await Get.dialog<bool>(AlertDialog(title: const Text('Xoá bài tập này và mọi bài đã nộp?'), actions: [
              TextButton(onPressed: () => Get.back(result: false), child: const Text('Huỷ')),
              FilledButton(onPressed: () => Get.back(result: true), child: const Text('Xoá')),
            ]));
            if (ok != true) return;
            try {
              await ClassworkApi.remove(asInt(a['id']));
              Get.back();
            } catch (e) {
              _fail(e);
            }
          },
          child: Text('Xoá', style: TextStyle(color: AppColors.error)),
        ),
      ]),
      SizedBox(height: 8.h),
      FutureBuilder<List<Map<String, dynamic>>>(
        future: _rows,
        builder: (context, snap) {
          if (!snap.hasData) return const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()));
          final rows = snap.data!;
          return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Bài nộp (${rows.where((r) => r['submission'] != null).length}/${rows.length})',
                style: const TextStyle(fontWeight: FontWeight.w800)),
            for (final r in rows)
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text('${asMap(r['user'])['display_name']}'),
                subtitle: r['submission'] == null
                    ? const Text('Chưa nộp')
                    : Text('${_when(r['submission']['submitted_at'])}${r['submission']['late'] == true ? ' · muộn' : ''}'),
                trailing: r['submission'] == null
                    ? null
                    : r['submission']['graded_at'] != null
                        ? _chip('${_fmt(r['submission']['score'])}/${_fmt(r['submission']['max_score'])}', AppColors.success)
                        : _chip('Chấm', AppColors.primary),
                onTap: r['submission'] == null
                    ? null
                    : () async {
                        await Get.to(() => GradeView(a: a, sid: asInt(r['submission']['id'])));
                        setState(() => _rows = ClassworkApi.submissions(asInt(a['id'])));
                      },
              ),
          ]);
        },
      ),
    ]);
  }
}

class GradeView extends StatefulWidget {
  const GradeView({super.key, required this.a, required this.sid});

  final Map<String, dynamic> a;
  final int sid;

  @override
  State<GradeView> createState() => _GradeViewState();
}

class _GradeViewState extends State<GradeView> {
  late final Future<Map<String, dynamic>> _s = ClassworkApi.submission(asInt(widget.a['id']), widget.sid);
  final Map<int, num?> scores = {};
  final Map<int, String> notes = {};
  num? total;
  String feedback = '';
  bool saving = false;
  bool _filled = false;

  void _fill(Map<String, dynamic> s) {
    if (_filled) return;
    _filled = true;
    for (final x in asMapList(s['answers'])) {
      scores[asInt(x['id'])] = _num(x['score']);
      notes[asInt(x['id'])] = '${x['feedback'] ?? ''}';
    }
    total = _num(s['score']);
    feedback = '${s['feedback'] ?? ''}';
  }

  Future<void> _save(Map<String, dynamic> s) async {
    final questions = asMapList(widget.a['questions']);
    final kinds = {for (final q in questions) asInt(q['id']): q['kind']};
    final manual = asMapList(s['answers'])
        .where((x) => !['mcq', 'fill'].contains(kinds[asInt(x['question'])]) || scores[asInt(x['id'])] != _num(x['score']))
        .toList();
    if (manual.any((x) => scores[asInt(x['id'])] == null) || (questions.isEmpty && total == null)) {
      _toast('Còn câu chưa cho điểm');
      return;
    }
    setState(() => saving = true);
    try {
      await ClassworkApi.grade(asInt(widget.a['id']), widget.sid, {
        'answers': [for (final x in manual) {'answer': x['id'], 'score': scores[asInt(x['id'])], 'feedback': notes[asInt(x['id'])] ?? ''}],
        if (questions.isEmpty) 'score': total,
        'feedback': feedback,
      });
      Get.back();
      _toast('Đã chấm', 'Học viên nhận được thông báo');
    } catch (e) {
      _fail(e);
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Widget _scoreBox(num? value, num max, ValueChanged<num?> onChanged) => SizedBox(
        width: 70.w,
        child: TextFormField(
          initialValue: value == null ? '' : _fmt(value),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(isDense: true, suffixText: '/${_fmt(max)}'),
          onChanged: (v) => onChanged(num.tryParse(v.replaceAll(',', '.'))),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final questions = asMapList(widget.a['questions']);
    return FutureBuilder<Map<String, dynamic>>(
      future: _s,
      builder: (context, snap) {
        final s = snap.data;
        if (s != null) _fill(s);
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(title: Text(s == null ? 'Bài nộp' : 'Bài của ${asMap(s['user'])['display_name']}'), actions: [
            if (s != null) TextButton(onPressed: saving ? null : () => _save(s), child: const Text('Lưu điểm')),
          ]),
          body: s == null
              ? const Center(child: CircularProgressIndicator())
              : ListView(padding: EdgeInsets.all(16.w), children: [
                  Text('Nộp lúc ${_when(s['submitted_at'])}${s['late'] == true ? ' (muộn)' : ''}',
                      style: TextStyle(color: AppColors.textSecondary)),
                  if (questions.isEmpty) ...[
                    if ('${s['text'] ?? ''}'.isNotEmpty) Padding(padding: EdgeInsets.only(top: 8.h), child: Text('${s['text']}')),
                    if (s['attachment'] != null)
                      TextButton.icon(onPressed: () => _openUrl(s['attachment'] as String?), icon: const Icon(Icons.attach_file),
                          label: Text('${s['attachment_name']}')),
                    Row(children: [const Text('Điểm '), _scoreBox(total, _num(widget.a['points']) ?? 10, (v) => total = v)]),
                  ],
                  for (var i = 0; i < questions.length; i++)
                    Builder(builder: (_) {
                      final q = questions[i];
                      final x = asMapList(s['answers']).firstWhereOrNull((y) => asInt(y['question']) == asInt(q['id']));
                      final opts = asMapList(q['options']);
                      return Container(
                        margin: EdgeInsets.only(top: 10.h),
                        padding: EdgeInsets.all(12.w),
                        decoration: _card(),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text('Câu ${i + 1} (${_kinds[q['kind']]}): ${q['prompt']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                          if (q['kind'] == 'mcq')
                            Text('Chọn: ${x?['selected_option'] != null && asInt(x!['selected_option']) < opts.length ? opts[asInt(x['selected_option'])]['text'] : '—'}'
                                ' · Đúng: ${opts.firstWhereOrNull((o) => o['correct'] == true)?['text'] ?? ''}'),
                          if (q['kind'] == 'fill')
                            Text('Trả lời: ${x?['text'] ?? '—'} · Đáp án: ${(q['accepted_answers'] as List? ?? []).join(' / ')}'),
                          if ((q['kind'] == 'essay' || q['kind'] == 'file') && '${x?['text'] ?? ''}'.isNotEmpty) Text('${x!['text']}'),
                          if (x?['attachment'] != null)
                            TextButton.icon(onPressed: () => _openUrl(x['attachment'] as String?), icon: const Icon(Icons.attach_file),
                                label: Text('${x!['attachment_name']}')),
                          if (x != null)
                            Row(children: [
                              _scoreBox(scores[asInt(x['id'])], _num(q['points']) ?? 1, (v) => scores[asInt(x['id'])] = v),
                              SizedBox(width: 8.w),
                              Expanded(
                                child: TextFormField(
                                  initialValue: notes[asInt(x['id'])],
                                  decoration: const InputDecoration(isDense: true, hintText: 'Nhận xét câu này'),
                                  onChanged: (v) => notes[asInt(x['id'])] = v,
                                ),
                              ),
                            ]),
                        ]),
                      );
                    }),
                  SizedBox(height: 12.h),
                  TextFormField(
                    initialValue: feedback,
                    minLines: 2,
                    maxLines: 5,
                    decoration: const InputDecoration(labelText: 'Nhận xét chung'),
                    onChanged: (v) => feedback = v,
                  ),
                ]),
        );
      },
    );
  }
}

// ---------------------------------------------------------------- member: doing the work

class _DoPanel extends StatefulWidget {
  const _DoPanel({required this.a, required this.onChanged});

  final Map<String, dynamic> a;
  final ValueChanged<Map<String, dynamic>> onChanged;

  @override
  State<_DoPanel> createState() => _DoPanelState();
}

class _DoPanelState extends State<_DoPanel> {
  late Map<String, dynamic> a = widget.a;
  final Map<int, Map<String, dynamic>> answers = {};
  final Map<String, PlatformFile> files = {};
  String text = '';
  bool sending = false;

  @override
  void initState() {
    super.initState();
    final mine = a['my_submission'] as Map?;
    if (mine != null) {
      for (final x in asMapList(mine['answers'])) {
        answers[asInt(x['question'])] = {'selected_option': x['selected_option'], 'text': x['text'] ?? ''};
      }
      text = '${mine['text'] ?? ''}';
    }
  }

  bool get done => (a['my_submission'] as Map?)?['graded_at'] != null;
  bool get closed {
    final due = DateTime.tryParse('${a['due_at'] ?? ''}');
    return a['status'] != 'published' || (due != null && due.isBefore(DateTime.now()) && a['allow_late'] == false);
  }

  Future<void> _submit() async {
    setState(() => sending = true);
    try {
      final x = await ClassworkApi.submit(asInt(a['id']), [
        for (final q in asMapList(a['questions'])) {'question': q['id'], ...?answers[asInt(q['id'])]},
      ], files, text);
      files.clear();
      setState(() => a = x);
      widget.onChanged(x);
      _toast((x['my_submission'] as Map?)?['graded_at'] != null ? 'Đã nộp và chấm xong' : 'Đã nộp bài');
    } catch (e) {
      _fail(e);
    } finally {
      if (mounted) setState(() => sending = false);
    }
  }

  Widget _filePick(String key, Map? submittedAnswer) {
    return Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 8.w, children: [
      if (submittedAnswer?['attachment'] != null)
        ActionChip(avatar: const Icon(Icons.attach_file, size: 18), label: Text('${submittedAnswer!['attachment_name']} (đã nộp)'),
            onPressed: () => _openUrl(submittedAnswer['attachment'] as String?)),
      if (files[key] != null) Chip(label: Text(files[key]!.name), onDeleted: () => setState(() => files.remove(key))),
      if (!done && !closed)
        OutlinedButton.icon(onPressed: () async {
          final f = await _pick();
          if (f != null) setState(() => files[key] = f);
        }, icon: const Icon(Icons.upload_file_rounded), label: const Text('Chọn file')),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final mine = a['my_submission'] as Map?;
    final questions = asMapList(a['questions']);
    final mineAnswers = {for (final x in asMapList(mine?['answers'])) asInt(x['question']): x};
    return ListView(padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 32.h), children: [
      _header(a),
      if (mine != null)
        Container(
          margin: EdgeInsets.only(top: 10.h),
          padding: EdgeInsets.all(12.w),
          decoration: BoxDecoration(
              color: (done ? AppColors.success : AppColors.primary).withValues(alpha: 0.08), borderRadius: BorderRadius.circular(12.r)),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(done
                ? 'Đã chấm: ${_fmt(mine['score'])}/${_fmt(mine['max_score'])} điểm${mine['percent'] != null ? ' (${mine['percent']}%)' : ''}'
                : 'Đã nộp lúc ${_when(mine['submitted_at'])}${mine['late'] == true ? ' (muộn)' : ''} – chờ chấm. Bạn vẫn sửa và nộp lại được.',
                style: const TextStyle(fontWeight: FontWeight.w700)),
            if ('${mine['feedback'] ?? ''}'.isNotEmpty) Text('${mine['feedback']}'),
          ]),
        ),
      SizedBox(height: 10.h),
      if (questions.isEmpty)
        Container(
          padding: EdgeInsets.all(12.w),
          decoration: _card(),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            TextFormField(
              initialValue: text,
              enabled: !done && !closed,
              minLines: 4,
              maxLines: 14,
              decoration: const InputDecoration(hintText: 'Bài làm của bạn (hoặc chụp bài làm rồi đính kèm)'),
              onChanged: (v) => text = v,
            ),
            SizedBox(height: 8.h),
            _filePick('file', mine),
          ]),
        ),
      for (var i = 0; i < questions.length; i++)
        Builder(builder: (_) {
          final q = questions[i];
          final qid = asInt(q['id']);
          final val = answers.putIfAbsent(qid, () => {'selected_option': null, 'text': ''});
          final r = mineAnswers[qid];
          final opts = asMapList(q['options']);
          return Container(
            margin: EdgeInsets.only(bottom: 10.h),
            padding: EdgeInsets.all(12.w),
            decoration: _card(),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Expanded(child: Text('Câu ${i + 1}. ${q['prompt']}', style: const TextStyle(fontWeight: FontWeight.w600))),
                Text('${_fmt(q['points'])} đ', style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
                if (done && r != null && r['is_correct'] != null)
                  Icon(r['is_correct'] == true ? Icons.check_circle : Icons.cancel,
                      color: r['is_correct'] == true ? AppColors.success : AppColors.error, size: 20.sp),
              ]),
              if (q['kind'] == 'mcq')
                for (var j = 0; j < opts.length; j++)
                  RadioListTile<int>(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    value: j,
                    groupValue: val['selected_option'] == null ? null : asInt(val['selected_option']),
                    onChanged: done || closed ? null : (v) => setState(() => val['selected_option'] = v),
                    title: Text('${String.fromCharCode(65 + j)}. ${opts[j]['text']}',
                        style: TextStyle(color: done && opts[j]['correct'] == true ? AppColors.success : null,
                            fontWeight: done && opts[j]['correct'] == true ? FontWeight.w700 : null)),
                  ),
              if (q['kind'] == 'fill')
                TextFormField(initialValue: '${val['text'] ?? ''}', enabled: !done && !closed,
                    decoration: const InputDecoration(hintText: 'Câu trả lời'), onChanged: (v) => val['text'] = v),
              if (q['kind'] == 'essay' || q['kind'] == 'file')
                TextFormField(
                  initialValue: '${val['text'] ?? ''}',
                  enabled: !done && !closed,
                  minLines: q['kind'] == 'essay' ? 3 : 1,
                  maxLines: 12,
                  decoration: InputDecoration(hintText: q['kind'] == 'essay' ? 'Câu trả lời của bạn' : 'Ghi chú (không bắt buộc)'),
                  onChanged: (v) => val['text'] = v,
                ),
              if (q['kind'] == 'file') Padding(padding: EdgeInsets.only(top: 6.h), child: _filePick('file_$qid', r)),
              if (done && r != null && (r['score'] != null || '${r['feedback'] ?? ''}'.isNotEmpty))
                Text('${_fmt(r['score'])}/${_fmt(q['points'])} điểm${'${r['feedback'] ?? ''}'.isNotEmpty ? ' – ${r['feedback']}' : ''}',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp)),
              if (done && q['kind'] == 'fill' && q['accepted_answers'] != null)
                Text('Đáp án: ${(q['accepted_answers'] as List).join(' / ')}', style: TextStyle(color: AppColors.success, fontSize: 13.sp)),
              if (done && '${q['explanation'] ?? ''}'.isNotEmpty)
                Text('${q['explanation']}', style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp)),
            ]),
          );
        }),
      if (!done && !closed)
        FilledButton.icon(
          onPressed: sending ? null : _submit,
          icon: sending ? SizedBox(width: 16.w, height: 16.w, child: const CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.send_rounded),
          label: Text(mine != null ? 'Nộp lại' : 'Nộp bài'),
        ),
      if (closed && mine == null)
        Text('Bài tập đã đóng hoặc đã quá hạn nộp.', style: TextStyle(color: AppColors.error), textAlign: TextAlign.center),
    ]);
  }
}

// ---------------------------------------------------------------- invitations

class GroupInvite {
  GroupInvite._();

  /// From a notification "… mời bạn vào nhóm …": accept or decline here.
  static Future<void> open(int groupId) async {
    final g = await CommunityRepository.group(groupId);
    if (!g.isInvited) {
      _toast(g.name, g.isMember ? 'Bạn đã ở trong nhóm này.' : 'Lời mời không còn hiệu lực.');
      return;
    }
    final ok = await Get.dialog<bool>(AlertDialog(
      title: Text('Vào nhóm ${g.name}?'),
      content: Text(g.description.isEmpty ? 'Bạn được mời vào nhóm học này.' : g.description),
      actions: [
        TextButton(onPressed: () => Get.back(result: false), child: const Text('Từ chối')),
        FilledButton(onPressed: () => Get.back(result: true), child: const Text('Nhận lời')),
      ],
    ));
    if (ok == null) return;
    try {
      if (ok) {
        await CommunityRepository.join(groupId);
        _toast('Đã vào nhóm ${g.name}', 'Xem bài tập và trò chuyện trong tab Nhóm học.');
      } else {
        await CommunityRepository.leave(groupId);
      }
    } catch (e) {
      _fail(e);
    }
  }
}
