# -*- coding: utf-8 -*-
# Text translations for Japanese (ja).
# Automatically generated - DO NOT EDIT, edit ja.po instead!
meta = {
  'language': 'Japanese',
  'maintainer': 'Jyunji Kondo <j-kondo@pst.fujitsu.com>',
  'encoding': 'utf-8',
  'direction': 'ltr',
}
text = {
'''(last edited %(time)s by %(editor)s)''':
'''(%(editor)sにより%(time)s回編集されました)''',
'''(last modified %s)''':
'''(最終更新日時 %s)''',
'''The backupped content of this page is deprecated and will not be included in search results!''':
'''このページは、deprecatedの印が付けられているので、検索結果には含まれません!''',
'''Version as of %(date)s''':
'''%(date)s のバージョン''',
'''Redirected from page "%(page)s"''':
'''"%(page)s"からリダイレクトされました''',
'''This page redirects to page "%(page)s"''':
'''このページは"%(page)s"にリダイレクトしています。''',
'''<p><small>If you submit this form, the submitted values will be displayed.
To use this form on other pages, insert a
<br><br><strong><tt>&nbsp;&nbsp;&nbsp;&nbsp;[[Form("%(pagename)s")]]</tt></strong><br><br>
macro call.</small></p>
''':
'''<p><small>このフォームを提出すると、提出された値が表示されます。
このフォームを別のページで使うには、
<br><br><strong><tt>&nbsp;&nbsp;&nbsp;&nbsp;[[Form("%(pagename)s")]]</tt></strong><br><br>
マクロを埋め込んでください。</b></small></p>
''',
'''You are not allowed to view this page.''':
'''あなたにはこのページを見る許可がありません!''',
'''RefreshCache''':
'''キャッシュを更新する''',
'''for this page (cached %(date)s)''':
''' (このページの %(date)s のキャッシュ)''',
'''Create this page''':
'''このページを作ってください。''',
'''Alternatively, use one of these templates:''':
'''かわりに、次のひな型も使ってください:''',
'''To create your own templates, add a page with a name matching the regex "%(page_template_regex)s".''':
'''あなた自身のひな型を作るには、"%(page_template_regex)s"の正規表現に一致するページを追加してください。''',
'''The following pages with similar names already exist...''':
'''似たような名前の次のページがすでに存在します...''',
'''You are not allowed to edit this page.''':
'''あなたは、このページを編集することができません!''',
'''Page is immutable!''':
'''ページは不変です！''',
'''Cannot edit old revisions!''':
'''古いリビジョンが編集できません！''',
'''The lock you held timed out, be prepared for editing conflicts!''':
'''あなたが保持していたロックはタイムアウトしました。不一致を編集する準備をしてください！''',
'''Edit "%(pagename)s"''':
'''"%(pagename)s"を編集''',
'''Preview of "%(pagename)s"''':
'''"%(pagename)s"のプレビュー''',
'''Your edit lock on %(lock_page)s has expired!''':
'''あなたの%(lock_page)sに対する編集ロックは、期限切れになりました！''',
'''Your edit lock on %(lock_page)s will expire in # minutes.''':
'''あなたの%(lock_page)sに対する編集ロックは、# 分後に期限切れになります。''',
'''Your edit lock on %(lock_page)s will expire in # seconds.''':
'''あなたの%(lock_page)sに対する編集ロックは、# 秒後に期限切れになります。''',
'''Someone else deleted this page while you were editing!''':
'''あなたが編集している間に、誰かがこのページを削除しました！''',
'''Someone else changed this page while you were editing!''':
'''あなたが編集している間に、誰かがこのページを変更しました！''',
'''Someone else saved this page while you were editing!
Please review the page and save then. Do not save this page as it is!
Have a look at the diff of %(difflink)s to see what has been changed.''':
'''あなたが編集している間に、誰かがこのページを保存しました！
ページをレビューして保存してください。このままこのページを保存しないでください！
何が変更されたか%(difflink)sの差分を見てください。''',
'''[Content of new page loaded from %s]''':
'''[新しいページの内容が%sからロードされました]''',
'''[Template %s not found]''':
'''[ひな型 %s が見つかりません]''',
'''Reduce editor size''':
'''エディタを縮小する。''',
'''Skip to preview''':
'''プレビューへ移動''',
'''[current page size <strong>%(size)d</strong> bytes]''':
'''[現在のページサイズは、<strong>%(size)d</strong>バイトです]''',
'''Describe %s here.''':
'''ここに %s について記述して！''',
'''Optional comment about this change''':
'''この修正についてのコメント''',
'''<No addition>''':
'''<追加なし>''',
'''Make this page belong to category %(category)s''':
'''このページを%(category)sカテゴリに登録してください''',
'''Check Spelling''':
'''綴りを確認''',
'''Save Changes''':
'''変更内容を保存する''',
'''Cancel''':
'''取消''',
'''By hitting <strong>%(save_button_text)s</strong> you put your changes under the %(license_link)s.
If you don\'t want that, hit <strong>%(cancel_button_text)s</strong> to cancel your changes.''':
'''<strong>%(save_button_text)s</strong>を押すと、あなたの変更を%(license_link)sに置きます。
または、<strong>%(cancel_button_text)s</strong>を押してキャンセルしてください。''',
'''Preview''':
'''プレビュー''',
'''Send mail notification''':
'''メール通知を送る''',
'''Remove trailing whitespace from each line''':
'''各行で末尾の空白を取り除く。''',
'''<dt>Emphasis:</dt>
<dd>\'\'<em>italics</em>\'\'; \'\'\'<strong>bold</strong>\'\'\'; \'\'\'\'\'<strong><em>bold italics</em></strong>\'\'\'\'\';
    \'\'<em>mixed \'\'\'<strong>bold</strong>\'\'\' and italics</em>\'\'; ---- horizontal rule.</dd>
<dt>Headings:</dt>
<dd>= Title 1 =; == Title 2 ==; === Title 3 ===;
    ==== Title 4 ====; ===== Title 5 =====.</dd>
<dt>Lists:</dt>
<dd>space and one of * bullets; 1., a., A., i., I. numbered items;
    1.#n start numbering at n; space alone indents.</dd>
<dt>Links:</dt>
<dd>JoinCapitalizedWords; ["brackets and double quotes"];
    url; [url]; [url label].</dd>
<dt>Tables:</dt>
<dd>|| cell text |||| cell text spanning two columns ||;
    no trailing white space allowed after tables or titles.</dd>
''':
'''<dt>強調:</dt>
<dd>\'\'<em>イタリック体</em>\'\'; \'\'\'<strong>ボールド体</strong>\'\'\'; \'\'\'\'\'<strong><em>ボールドイタリック体</em></strong>\'\'\'\'\';
    \'\'<em>混合 \'\'\'<strong>ボールド体</strong>\'\'\' そして イタリック体</em>\'\'; ---- 水平線。</dd>
<dt>表題:</dt>
<dd>= タイトル 1 =; == タイトル 2 ==; === タイトル 3 ===;
    ==== タイトル 4 ====; ===== タイトル 5 =====.</dd>
<dt>リスト:</dt>
<dd>「空白と１つの*」でビュレット; 「1., a., A., i., I.」で番号付きアイテム;
    「1.#n」で、nからの番号を付けます; 「空白」でインデント。</dd>
<dt>リンク:</dt>
<dd>JoinCapitalizedWords; ["ブラケットとダブルクォート"];
    url; [url]; [url ラベル]。</dd>
<dt>テーブル:</dt>
<dd>|| セルの文章 |||| ２つの桁に広がったセルの文章 ||;
    テーブルやタイトルの行末に空白を置いてはいけません。</dd>
''',
'''Edit was cancelled.''':
'''編集は取り消されました。''',
'''Dear Wiki user,

You have subscribed to a wiki page or wiki category on "%(sitename)s" for change notification.

The following page has been changed by %(editor)s:
%(pagelink)s

''':
'''Wikiユーザのみなさんへ

あなたは"%(sitename)s"上のwikiページまたはwikiカテゴリの変更通知を受け取ります。
次のページは%(editor)sにより変更されました:
%(pagelink)s

''',
'''The comment on the change is:
%(comment)s

''':
'''修正時のコメント:
%(comment)s

''',
'''No older revisions of the page stored, diff not available.''':
'''このページの古いリビジョンはありません。よって差分はありません。''',
'''No differences found!
''':
'''違いが見つかりませんでした!
''',
'''The diff function returned with error code %(rc)s!''':
'''差分機能がエラーコード %(rc)sで復帰しました！''',
'''[%(sitename)s] Update of "%(pagename)s"''':
'''[%(sitename)s]"%(pagename)s"の更新''',
'''You will not be notified of your own changes!''':
'''あなた自身の変更は通知されません！''',
'''Status of sending notification mails:''':
'''メイル通知の状態:''',
'''[%(lang)s] %(recipients)s: %(status)s''':
'''[%(lang)s] %(recipients)s: %(status)s''',
'''Nobody subscribed to this page, no mail sent.''':
'''だれもこのページを購読していないので、メールは送られません。''',
'''## backup of page "%(pagename)s" submitted %(date)s''':
'''## "%(pagename)s"のバックアップは%(date)sに実行されました''',
'''You are not allowed to edit this page!''':
'''あなたは、このページを編集できません！''',
'''You cannot save empty pages.''':
'''空のページはセーブできません。''',
'''Sorry, someone else saved the page while you edited it.
<p>Please do the following: Use the back button of your browser, and cut&paste
your changes from there. Then go forward to here, and click EditText again.
Now re-add your changes to the current page contents.</p>
<p><em>Do not just replace
the content editbox with your version of the page, because that would
delete the changes of the other person, which is excessively rude!</em></p>
''':
'''<b>残念ですが、あなたが編集している間にページが保存されました。
<p>以下を行ってください：ブラウザの「戻る」ボタンを使って編集ページに戻り、あなたが変更した箇所をカットしてください。
それから「進む」ボタンでここに戻り「ここで編集して！」をクリックしてください。
そして、あなたの修正をペーストしてください。
<p><em>あなたが編集していた内容で置き換えないでください！
そうすると他の人の変更が消されてしまいます(これはとても失礼なことです！)。</em></p>
''',
'''A backup of your changes is <a href="%(backup_url)s">here</a>.''':
'''あなたの変更のバックアップは、<a href="%(backup_url)s">ここ</a>にあります。''',
'''You did not change the page content, not saved!''':
'''ページは変更されていないので、保存されません！''',
'''You can\'t change ACLs on this page since you have no admin rights on it!''':
'''権利がないので、このページのACLを変更できません！''',
'''Thank you for your changes. Your attention to detail is appreciated.''':
'''変更してくれてありがとう。感謝します。''',
'''The lock of %(owner)s timed out %(mins_ago)d minute(s) ago, and you were granted the lock for this page.''':
'''%(owner)sのロックは、%(mins_ago)d分前にタイムアウトしました。そして、このページのロックはあなたに与えられました''',
'''Other users will be <em>blocked</em> from editing this page until %(bumptime)s.''':
'''他のユーザは、%(bumptime)s まで、このページを編集することがブロックされます。''',
'''Other users will be <em>warned</em> until %(bumptime)s that you are editing this page.''':
'''他のユーザは、あなたが編集している %(bumptime)s までの間警告されます。''',
'''Use the Preview button to extend the locking period.''':
'''ロック期間を延長するためにプレビューボタンを使ってください。''',
'''This page is currently <em>locked</em> for editing by %(owner)s until %(timestamp)s, i.e. for %(mins_valid)d minute(s).''':
'''このページは、現在%(owner)sにより%(timestamp)sまで編集することがロックされています。すなわち、%(mins_valid)d 分間。''',
'''This page was opened for editing or last previewed at %(timestamp)s by %(owner)s.<br>
<strong class="highlight">You should <em>refrain from editing</em> this page for at least another %(mins_valid)d minute(s),
to avoid editing conflicts.</strong><br>
To leave the editor, press the Cancel button.''':
'''このページは、%(timestamp)sに%(owner)sにより、編集またはプレビューのためオープンされました。<br>
<strong class="highlight">あなたは、少なくとも%(mins_valid)dの間、不一致をさけるためにこのページを編集することを控えるべきです。</strong><br>
キャンセルボタンでエディタから抜けてください。''',
'''<unknown>''':
'''<不明>''',
'''Diffs''':
'''差分''',
'''Info''':
'''情報''',
'''Edit''':
'''編集''',
'''UnSubscribe''':
'''購読中止''',
'''Subscribe''':
'''購読''',
'''Raw''':
'''生''',
'''XML''':
'''XML''',
'''Print''':
'''印刷''',
'''View''':
'''見る''',
'''Home''':
'''ホーム''',
'''Up''':
'''上''',
'''Unknown action''':
'''未定義のアクション''',
'''Can\'t work out query''':
'''問い合わせに応じられません。''',
'''Open editor on double click''':
'''ダブルクリックでエディターを開く''',
'''Remember last page visited''':
'''最後の訪問ページを記憶する''',
'''Show emoticons''':
'''emoticonを表示する''',
'''Show fancy links''':
'''fancy linkを表示する''',
'''Show question mark for non-existing pagelinks''':
'''存在しないページリンクへはクエスチョンマークを表示する''',
'''Show page trail''':
'''ページトレールを表示する''',
'''Show icon toolbar''':
'''アイコンツールバーを表示する''',
'''Show top/bottom links in headings''':
'''表題に先頭/末尾へのリンクを表示する''',
'''Show fancy diffs''':
'''fancy diffを表示する''',
'''Add spaces to displayed wiki names''':
'''表示されるwiki nameに空白を挿入する''',
'''Remember login information forever''':
'''ログイン情報を永久に記憶する''',
'''Disable this account forever''':
'''このアカウントを永久に無効にする''',
'''Cookie deleted. You are now logged out.''':
'''クッキーが削除されました。あなたはログアウトしました。''',
'''This wiki is not enabled for mail processing. Contact the owner of the wiki, who can either enable email, or remove the "Subscribe" icon.''':
'''このwikiでは、メイル処理が利用できません。wikiのオーナーにコンタクトして、メイルを使えるようにするか、"講読"アイコンを削除してもらってください。''',
'''Please provide a valid email address!''':
'''<b>正しいemailアドレスを入力してください!</b>''',
'''Found no account matching the given email address \'%(email)s\'!''':
'''与えられたemailアドレス \'%(email)s\' に該当するアカウントが見つかりません!''',
'''Unknown user name or password.''':
'''ユーザ名またはパスワードが正しくありません。''',
'''Please enter a user name!''':
'''ユーザ名を入力してください！''',
'''User name already exists!''':
'''ユーザ名が既に存在しています！''',
'''Passwords don\'t match!''':
'''パスワードが間違っています！''',
'''Please enter your name like that: FirstnameLastname''':
'''FirstnameLastname のように名前を入力してください''',
'''Please provide your email address - without that you could not get your login data via email just in case you lose it.''':
'''eメイルアドレスを入れてください。さもないとlogin dataを失くしたときに、eメイルで受け取れなくなります。''',
'''This user name already belongs to somebody else.''':
'''このユーザ名は、既に他の人につかわれています。''',
'''This email already belongs to somebody else.''':
'''このeメイルアドレスは、既に他の人につかわれています。''',
'''User preferences saved!''':
'''User preferencesを保存しました！''',
'''Default''':
'''省略値''',
'''<Browser setting>''':
'''<ブラウザの設定>''',
'''Save''':
'''保存''',
'''Logout''':
'''ログアウト''',
'''Login''':
'''ログイン''',
'''Create Profile''':
'''プロファイルを作成''',
'''Mail me my account data''':
''' アカウントデータをメールする ''',
'''Name''':
'''名前''',
'''(Use FirstnameLastname)''':
'''(FirstnameLastnameを使ってください)''',
'''Password''':
'''パスワード''',
'''Password repeat''':
'''パスワード再入力''',
'''(Only when changing passwords)''':
'''(パスワードを変更したときのみ)''',
'''Email''':
'''Ｅメール''',
'''Preferred theme''':
'''好みのテーマ''',
'''User CSS URL''':
'''CSSのURL''',
'''(Leave it empty for disabling user CSS)''':
'''(CSSを無効にするには空のままにしておく)''',
'''Editor size''':
'''エディタのサイズ''',
'''Time zone''':
'''タイムゾーン''',
'''Your time is''':
'''あなたの時間は''',
'''Server time is''':
'''サーバの時間は''',
'''Date format''':
'''日付の書式''',
'''Preferred language''':
'''好みの言語''',
'''General options''':
'''一般的なオプション''',
'''Quick links''':
'''クイックリンク''',
'''This list does not work, unless you have entered a valid email address!''':
'''このリストは、有効なemailアドレスを記入するまで機能しません!''',
'''Subscribed wiki pages (one regex per line)''':
'''購読されているwikiページ(1行あたり１つの正規表現)''',
'''Action''':
'''アクション''',
'''Please use a more selective search term instead of \'%(needle)s\'!''':
'''\'%(needle)s\'の代わりに、より具体的な検索語を使ってください!''',
'''Full text search for "%s"''':
'''"%s" の全文検索結果''',
'''match''':
''' 箇所が一致''',
'''matches''':
''' 箇所が一致''',
'''Title search for "%s"''':
'''"%s"のタイトル検索結果''',
'''%(hits)d hits out of %(pages)d pages searched.''':
'''%(pages)d ページで %(hits)d 個がヒット。''',
'''Needed %(timer).1f seconds.''':
'''%(timer).1f秒かかりました。''',
'''No older revisions available!''':
'''古いバージョンがありません!''',
'''Diff for "%s"''':
'''"%s"の差分''',
'''Differences between versions dated %s and %s''':
'''日付が %s と %s のバージョンでの差分''',
'''(spanning %d versions)''':
'''(%d バージョンの隔たり)''',
'''No differences found!''':
'''違いが見つかりませんでした!''',
'''The page was saved %(count)d times, though!''':
'''このページは %(count)d回保存されました!''',
'''Ignore changes in the amount of whitespace''':
'''空白のみの変更を無視する''',
'''General Information''':
'''一般的な情報''',
'''Page size: %d''':
'''ページサイズ：%d''',
'''SHA digest of this page\'s content is:''':
'''このページのSHAダイジェストは：''',
'''The following users subscribed to this page:''':
'''このページを購読するようにしました。''',
'''This page links to the following pages:''':
'''このページは以下のページへリンクしています:''',
'''Revision History''':
'''更新履歴''',
'''Date''':
'''日付''',
'''Size''':
'''サイズ''',
'''Diff''':
'''差分''',
'''Editor''':
'''編集者''',
'''Comment''':
'''コメント''',
'''view''':
'''見る''',
'''raw''':
'''原文''',
'''print''':
'''印刷''',
'''revert''':
'''戻る''',
'''Revert to version dated %(datestamp)s.''':
'''%(datestamp)sの日付のバージョンに戻す。''',
'''N/A''':
'''N/A''',
'''Info for "%s"''':
'''"%s"の情報''',
'''Show "%(title)s"''':
'''"%(title)s"を表示''',
'''General Page Infos''':
'''一般的な情報''',
'''Show chart "%(title)s"''':
'''"%(title)s"のチャートを表示''',
'''Page hits and edits''':
'''ページのヒットと編集''',
'''You are not allowed to revert this page!''':
'''あなたはこのwikiでページを戻すことを許可されていません!''',
'''An error occurred while reverting the page.''':
'''このページを戻す最中にエラーが起きました。''',
'''You are not allowed to subscribe to a page you can\'t read.''':
'''あなたが読めないページを、購読することはできません。''',
'''You didn\'t create a user profile yet. Select UserPreferences in the upper right corner to create a profile.''':
'''あなたはまだ、プロフィールを作っていません。右上の角のUserPreferencesを選択して作ってください。''',
'''You didn\'t enter an email address in your profile. Select your name (UserPreferences) in the upper right corner and enter a valid email address.''':
'''プロフィールにeメイルアドレスを入力していません。右上の角のUserPreferencesであなたの名前を選び、正しいeメイルアドレスを入力してください。''',
'''You are already subscribed to this page.''':
'''あなたは既にこのページを購読しています。''',
'''To unsubscribe, go to your profile and delete this page from the subscription list.''':
'''購読しないようにするには、プロファイルへ行って購読リストから、このページを削除してください。''',
'''You have been subscribed to this page.''':
'''このページを購読するようにしました。''',
'''Required attribute "%(attrname)s" missing''':
'''必要な属性 "%(attrname)s" がありません''',
'''Submitted form data:''':
'''提出されたフォームデータ:''',
'''Display context of search results''':
'''検索結果の内容を表示する''',
'''Case-sensitive searching''':
'''大小文字を区別して検索''',
'''Go''':
'''実行''',
'''Include system pages''':
'''システムページを含む''',
'''Exclude system pages''':
'''システムページを含まない''',
'''Plain title index''':
'''平文タイトルの索引''',
'''XML title index''':
'''XMLのタイトル索引''',
'''Python Version''':
'''Pythonのバージョン''',
'''MoinMoin Version''':
'''MoinMoinのバージョン''',
'''Release %s [Revision %s]''':
'''リリース %s [版数 %s]''',
'''4Suite Version''':
'''4Suiteのバージョン''',
'''Number of pages''':
'''ページの数''',
'''Number of system pages''':
'''システムページの数''',
'''Number of backup versions''':
'''バックアップされたバージョン数''',
'''Accumulated page sizes''':
'''累計ページサイズ''',
'''Entries in edit log''':
'''編集ログ中のエントリー数''',
'''%(logcount)s (%(logsize)s bytes)''':
'''%(logcount)s (%(logsize)s バイト)''',
'''NONE''':
'''NONE''',
'''Global extension macros''':
'''グローバル拡張マクロ''',
'''Local extension macros''':
'''ローカル拡張マクロ''',
'''Global extension actions''':
'''グローバル拡張アクション''',
'''Local extension actions''':
'''ローカル拡張アクション''',
'''Installed processors''':
'''インストールされたプロセッサ''',
'''ERROR in regex \'%s\'''':
'''正規表現 \'%s\' でエラーがありました。''',
'''Bad timestamp \'%s\'''':
'''不正な時刻 \'%s\'''',
'''Expected "=" to follow "%(token)s"''':
'''"%(token)s" の後に"="がありません''',
'''Expected a value for key "%(token)s"''':
'''"%(token)s" キーに値がありません''',
'''Wiki Markup''':
'''Wiki マークアップ''',
'''Print View''':
'''印刷ビュー''',
'''[%d attachments]''':
'''[%d 個の添付ファイル]''',
'''There are <a href="%(link)s">%(count)s attachment(s)</a> stored for this page.''':
'''このページには <a href="%(link)s">%(count)s 個の添付ファイル</a> が保存されています。''',
'''Filename of attachment not specified!''':
'''添付ファイル名が指定されていません！''',
'''Attachment \'%(filename)s\' does not exist!''':
'''\'%(filename)s\'というファイルが存在しません！''',
'''<p>To refer to attachments on a page, use <strong><tt>attachment:filename</tt></strong>, 
as shown below in the list of files. 
Do <strong>NOT</strong> use the URL of the <tt>[get]</tt> link, 
since this is subject to change and can break easily.</p>''':
'''<p>このページの添付ファイルを参照するには、以下にリストされている<strong><tt>attachment:ファイル名</tt></strong>を使ってください。
変更されやすく簡単に壊れてしまうので<tt>[get]</tt>リンクのURLは使わないでください。''',
'''del''':
'''削除する''',
'''get''':
'''取る''',
'''edit''':
'''編集する''',
'''No attachments stored for %(pagename)s''':
'''%(pagename)s の添付ファイルは保存されませんでした''',
'''Edit drawing''':
'''絵を編集する''',
'''Attached Files''':
'''添付ファイル''',
'''You are not allowed to attach a file to this page.''':
'''あなたはこのページにファイルを添付することができません。''',
'''New Attachment''':
'''添付ファイルを追加''',
'''An upload will never overwrite an existing file. If there is a name
conflict, you have to rename the file that you want to upload.
Otherwise, if "Rename to" is left blank, the original filename will be used.''':
'''アップロードでは、既存のファイルを上書きしません。 同じ名前のものがあれば、
アップロードしたいファイルの名前を変えてください。
"名前を変更"が空白の場合、オリジナルのファイル名が使われます。''',
'''File to upload''':
'''アップロードするファイル''',
'''MIME Type (optional)''':
'''MIMEタイプ (任意)''',
'''Save as''':
'''保存''',
'''Upload''':
'''アップロード''',
'''File attachments are not allowed in this wiki!''':
'''このwikiでファイルの添付はできません！''',
'''You are not allowed to save a drawing on this page.''':
'''あなたはこのページで絵を保存することができません!''',
'''You are not allowed to delete attachments on this page.''':
'''添付ファイルを削除することを許可されていません。''',
'''You are not allowed to get attachments from this page.''':
'''添付ファイルを得ることを許可されていません。''',
'''You are not allowed to view attachments of this page.''':
'''添付ファイルを見ることを許可されていません。''',
'''Unsupported upload action: %s''':
'''<b>サポートされていないアップロードアクション: %s</b>''',
'''Attachments for "%(pagename)s"''':
'''"%(pagename)s の添付ファイル"''',
'''Attachment \'%(target)s\' (remote name \'%(filename)s\') already exists.''':
'''添付ファイル \'%(target)s\' (リモート名 \'%(filename)s\')は既に存在しています。''',
'''Attachment \'%(target)s\' (remote name \'%(filename)s\') with %(bytes)d bytes saved.''':
'''添付ファイル \'%(target)s\' (リモート名 \'%(filename)s\') %(bytes)d バイトが保存されました。''',
'''Attachment \'%(filename)s\' deleted.''':
'''\'添付ファイル \'%(filename)s\' が削除されました。''',
'''Attachment \'%(filename)s\'''':
'''添付ファイル \'%(filename)s\'''',
'''Unknown file type, cannot display this attachment inline.''':
'''ファイルタイプが不明です。インラインで表示できません。''',
'''attachment:%(filename)s of %(pagename)s''':
'''%(pagename)s の添付ファイル：%(filename)s''',
'''You are not allowed to delete this page.''':
'''あなたはこのページを削除することを許可されていません。''',
'''This page is already deleted or was never created!''':
'''このページは既に削除されているか、まだ作られていません!''',
'''Please use the interactive user interface to delete pages!''':
'''対話的なユーザインターフェースを使ってページを削除してください!''',
'''Page "%s" was successfully deleted!''':
'''"%s"は正常に削除されました!''',
'''Really delete this page?''':
'''このページを本当に削除しますか？''',
'''Delete''':
'''削除''',
'''Optional reason for the deletion''':
'''削除の理由''',
'''No pages match "%s"!''':
'''"%s"で一致したページはありません!''',
'''Exactly one matching page for "%s" found!''':
'''"%s"に正確に一致したページが見つかりました！''',
'''Multiple matches for "%s...%s"''':
'''"%s...%s"で複数が一致しました。''',
'''You cannot use LikePages on an extended pagename!''':
'''拡張ページ名では、LikePagesを使えません!''',
'''%(matchcount)d %(matches)s for "%(title)s"''':
'''"%(title)s" が %(matchcount)d %(matches)s''',
'''Local Site Map for "%s"''':
'''"%s"のローカルサイトマップ''',
'''You are not allowed to rename pages in this wiki!''':
'''あなたはこのページの名前を変更することを許可されていません!''',
'''Please use the interactive user interface to rename pages!''':
'''対話的なユーザインターフェースを使ってページの名前を変更してください!''',
'''A page with the name "%s" already exists!''':
'''"%s"の名前のページが既に存在します！''',
'''Page "%s" was successfully renamed to "%s"!''':
'''"%s"は正常に名前が"%s"に変更されました!''',
'''Rename''':
'''名前を変更''',
'''New name''':
'''新しい名前''',
'''Optional reason for the renaming''':
'''名前の変更理由''',
'''(including %(localwords)d %(pagelink)s)''':
'''(%(pagelink)s の %(localwords)d を含む)''',
'''The following %(badwords)d words could not be found in the dictionary of %(totalwords)d words%(localwords)s and are highlighted below:''':
'''次の %(badwords)d 語は、%(totalwords)d 語の辞書 %(localwords)s でみつからず、下でハイライトされています:''',
'''Add checked words to dictionary''':
'''チェックされた語を辞書に追加する''',
'''No spelling errors found!''':
'''綴り間違いはありませんでした!''',
'''You can\'t check spelling on a page you can\'t read.''':
'''読めないページのスペルチェックはできません。''',
'''Full Link List for "%s"''':
'''"%s" の全リンクリスト''',
'''Invalid include arguments "%s"!''':
'''"%s" の引数が正しくありません!''',
'''Nothing found for "%s"!''':
'''"%s"について何も見つかりませんでした！''',
'''Unsupported navigation scheme \'%(scheme)s\'!''':
'''\'%(scheme)s\' のナビゲーション方法は、未サポートです！''',
'''No parent page found!''':
'''親ページが見つかりませんでした！''',
'''Wiki''':
'''Wiki''',
'''Slideshow''':
'''スライドショー''',
'''Start''':
'''スタート''',
'''Slide %(pos)d of %(size)d''':
'''スライド %(pos)d / %(size)d''',
'''No orphaned pages in this wiki.''':
'''このwikiで、孤立したページはありません。''',
'''No quotes on %(pagename)s.''':
'''%(pagename)s にクォートがありません。''',
'''Upload of attachment \'%(filename)s\'.''':
'''添付ファイル \'%(filename)s\' をアップロードします。''',
'''Drawing \'%(filename)s\' saved.''':
'''\'%(filename)s\'が保存されました。''',
'''%(hours)dh&nbsp;%(mins)dm&nbsp;ago''':
'''%(hours)d時間&nbsp;%(mins)d分&nbsp;前''',
'''(no bookmark set)''':
'''(ブックマークはありません。)''',
'''(currently set to %s)''':
'''(%sにセットされています)''',
'''Update my bookmark timestamp''':
'''ブックマークのタイムスタンプを更新する''',
'''set bookmark''':
'''ブックマークにセットする''',
'''[Bookmark reached]''':
'''[ブックマークが到達しました]''',
'''Markup''':
'''マークアップ''',
'''Display''':
'''表示''',
'''Filename''':
'''ファイル名''',
'''You need to provide a chart type!''':
'''チャートのタイプを指定してください！''',
'''Bad chart type "%s"!''':
'''"%s" は、誤ったチャートのタイプです！''',
'''Download XML export of this wiki''':
'''このwikiのXML exportをダウンロードする''',
'''No wanted pages in this wiki.''':
'''このwikiで、何も記述がないページはありません。''',
'''Create new drawing "%(filename)s"''':
'''新しい絵 "%(filename)s" を生成する''',
'''Upload new attachment "%(filename)s"''':
'''新しい添付ファイル"%(filename)s" をアップロードする''',
'''Edit drawing %(filename)s''':
'''%(filename)s を編集''',
'''Expected "%(wanted)s" after "%(key)s", got "%(token)s"''':
'''"%(key)s" の後に "%(wanted)s" がありません。"%(token)s"を使います''',
'''Expected an integer "%(key)s" before "%(token)s"''':
'''"%(token)s" の前に整数型の "%(key)s" がありません''',
'''Expected an integer "%(arg)s" after "%(key)s"''':
'''"%(key)s" の後に整数型の "%(arg)s" がありません''',
'''Expected a color value "%(arg)s" after "%(key)s"''':
'''"%(key)s" の後に色の指定の "%(arg)s" がありません''',
'''XSLT option disabled!''':
'''XSLTオプションが無効です！''',
'''XSLT processing is not available!''':
'''XSLT処理が利用できません！''',
'''%(errortype)s processing error''':
'''%(errortype)s の処理エラー''',
'''Charts are not available!''':
'''チャートが利用できません！''',
'''%(chart_title)s for %(filterpage)s''':
'''%(filterpage)s の %(chart_title)s''',
'''green=view
red=edit''':
'''緑=表示
赤=編集''',
'''date''':
'''日付''',
'''# of hits''':
'''ヒット回数''',
'''Page Size Distribution''':
'''ページサイズディストリビューション''',
'''page size upper bound [bytes]''':
'''ページサイズの上限 [バイト]''',
'''# of pages of this size''':
'''このサイズのページ数''',
'''Others''':
'''その他''',
'''Distribution of User-Agent Types''':
'''ユーザエージェントタイプのディストリビューション''',
'''Click here to do a full-text search for this title''':
'''このタイトルで全文検索するには、ここをクリックして下さい''',
'''Clear message''':
'''メッセージを消す。''',
'''ShowText''':
'''テキストを表示''',
'''of this page''':
'''！''',
'''EditText''':
'''テキストを編集''',
'''Immutable page''':
'''変わらないページ''',
'''FindPage''':
'''ページを見つける''',
'''SiteNavigation''':
'''サイトナビゲーション''',
'''or search titles %(titlesearch)s, full text %(textsearch)s or''':
'''、タイトル検索する %(titlesearch)s 、テキスト検索する %(textsearch)s または、''',
'''Or try one of these actions:''':
'''または、これらを試してみてください:''',
'''Show all changes in the last %s days.''':
'''過去 %s 日間のすべての変更を見る''',
'''Line''':
'''行''',
'''Deletions are marked like this.''':
'''削除された箇所はこのように表示されます。''',
'''Additions are marked like this.''':
'''追加された箇所はこのように表示されます。''',
'''Connection to mailserver \'%(server)s\' failed: %(reason)s''':
'''メイルサーバ \'%(server)s\' への接続が失敗しました: %(reason)s''',
'''Mail sent OK''':
'''メールは正しく送られました''',
'''FrontPage''':
'''フロントページ''',
'''RecentChanges''':
'''更新履歴''',
'''TitleIndex''':
'''タイトル索引''',
'''WordIndex''':
'''ワード索引''',
'''HelpContents''':
'''ヘルプ''',
'''HelpOnFormatting''':
'''整形に関するヘルプ''',
'''UserPreferences''':
'''ユーザ設定''',
'''WikiLicense''':
'''Wikiライセンス''',
'''Mon''':
'''月''',
'''Tue''':
'''火''',
'''Wed''':
'''水''',
'''Thu''':
'''木''',
'''Fri''':
'''金''',
'''Sat''':
'''土''',
'''Sun''':
'''日''',
}
