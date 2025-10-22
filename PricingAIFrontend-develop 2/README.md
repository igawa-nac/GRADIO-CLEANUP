# PricingAIFrontend
## 記事追加 : 
- このアプリの使い方についてまとめました。[当アプリの利用方法](docs/development/usage.md)
- シークレット(機密情報を含む環境変数)をdatabricks appsで扱う方法についてまとめました。[databricks Apps上での環境変数の利用方法(機密情報について)](docs/development/UseSecret.md)
- JobsへのAPIリストを作成しました。[APIの一覧](./docs/api/APIList.md)
- JobsへのGradioからの接続に関するドキュメントを追加しました。[databricks JobsとGradioのAPI接続について](./docs/development/JobsConnection.md)
- フロントエンドのコード規約ページを追加しました。[Frontendのコード規約](./docs/development/frontend.rules.md)
- チェックボックスをGradioで実装する際のサンプルコードを掲載しました。[チェックボックス](./docs/development/checkbox.md)
## GitHubやGitの使い方
### 最初に利用する場合
以下のドキュメントを参考にcloneを行ってください。

[GitHub 最初にすること](./docs/development/initial.md)

## 新しい機能を作るときに最初に行うこと
役割分担を明確にするために、新しい機能を作ろうと思ったら最初に以下の内容を実施してください。
<br/>※README.mdおよびdocumentsディレクトリ以下、docs/assets/imagesディレクトリ以下については以下の手順を踏まずにdevelopブランチに直接追加してかまいません。

### 1. issueを作成する。
以下のようにissueタブを開いてください。
![issueタブ](docs/assets/images/readme1.png)
New Issueをクリックしてください。
![New Issue](docs/assets/images/readme2.png)
基本的に伝わる内容を書けば問題ありませんが、**Assign Yourself**は忘れずにクリックしてください。押したら画面下のCreateをクリック。
![Assign Yourself](docs/assets/images/readme3.png)
こんな感じで作成されますが、以下の赤丸で囲んだ数字をこの後利用するので覚えておいてください。
![タイトル横の#がついた数字を覚えておく。](docs/assets/images/readme4.png)

### 2. ブランチを作成する。
IssueからCodeに戻ったら、ブランチ名のプルダウンボタン(基本的にはmain)をクリック。
![Codeをクリックして、ブランチ名(基本的にmain)をクリック](docs/assets/images/readme5.png)
**develop**をクリック
![developをクリック](docs/assets/images/readme6.png)

ブランチ名がdevelopになったことを確認する。
![ブランチがdevelopになったか確認](docs/assets/images/readme7.png)
ブランチ名のdevelopをクリック(同じ場所)
![ブランチ名のdevelopをクリック](docs/assets/images/readme7.png)

ブランチ名を入力する。
ブランチ名のルール
- 最初はfeature/(新機能の意味)
- issue番号(先ほど覚えておくように伝えた番号)を書いて、ハイフンを書く(例 : feature/21-)
- 問題の概要を短めの英語で書く(例 : feature/21-SetNewModal)。
    
    なお、単語の区切りはキャメルケース(例 : HeHasALotOfApple)とケバブケース(例 : he-has-a-lot-of-apple)のどちらも使われうると思うが、そのプロジェクトでどちらが使われてきたかを確認して合わせるのが一番よいと思う。
![ブランチ名を入力する](docs/assets/images/readme8.png)
Create branchをクリック
![Create branch ... をクリックする](docs/assets/images/readme9.png)

ブランチ名が変わっていれば成功
![ブランチ名が作成したブランチに代わっていれば成功](docs/assets/images/readme10.png)

### 3. ローカル(お手元のPCの環境)を作成したブランチに切り替える
1. cloneしたフォルダをVSCodeで開く
2. ターミナルを開く
3. 以下のコマンドを実行する
まずは
```shell
git fetch
```
次に
```shell
git checkout 作成したブランチ名
```
例えば
```shell
git checkout feature/1-CreateSpecialUI
```
そして
```shell
git pull
```
※ちなみにこの３つのコマンドの実行順序は結構適当でかまいません。checkoutを最初にするとエラーが出るなどありますが、エラーが出たら別のコマンドを実行して再度実行すれば特に問題ないことがほとんどだと思います。

## 毎回実行すること
**※注意 : 実行する前に自分のブランチで作業しているか確認してください。もしも誤ってmainやdevelop、他のブランチを利用していた場合はお伝えください。git stashというものを利用して変更を保持したまま別ブランチに移動します。**

コードを変更して、オンライン上に保存したい場合は、ターミナルで以下を実行する。
```shell
git status
```
このコマンドは単なる状態確認だが、Gitの仕組みに触れることができるので、少なくとも慣れるまでは実行するのを推奨する。ちなみにこのコマンドの出力をよく見ることでブランチ名も確認できる。
```shell
git add *
```
ファイルやフォルダの更新をGitに読み込ませる。*は「このディレクトリ以下すべて」という意味。
```shell
git status
```
これも必須ではないが慣れるまでは実行するとよい。慣れても普通に実行する。
```shell
git commit -m "コミットの名前"
```
このコマンドを実行することにより、ローカルに変更が保存される。今後の開発でバグが起きてもこの「コミット」がセーブ地点となってコードの状態については巻き戻すことができる。
```shell
git log
```
このコマンドも必須ではない。だが、コミットが成功しているか確認するためには便利である。
```shell
git push
```
このコマンドを実行することで変更がオンライン上(GitHub上)にアップロードされる。


