# GitHub 最初にすること
リポジトリのクローン
- あなたのパソコンのフォルダとオンライン上にあるGitHubをつなぐ作業
- 「リポジトリ」≒オンライン上のフォルダ

## GitHub リンク
```shell
https://github.com/y-tamama/PricingAIFrontend
```

## git clone
GitHubからクローンする。

---
以下のボタンをクリック
![GitHubページでCodeボタンをクリック](../assets/images/init1.png)
--- 
URLをコピー
![Codeボタンを押して開いたURL(末尾が.git)をコピー](../assets/images/init2.png)
--- 
コードをコピーしたいフォルダをVSCodeで開く。開いたら以下のようにターミナルが表示されているか確認する。されていなければCtrl+Jを同時押しする。(Ctrlを押して、そのままJを押す。)
![ターミナルを開く](../assets/images/init3.png)
---
---
以下のコマンドをターミナルで実行する。**ただしプロキシは切っておくこと。**
---
```shell
git clone 先ほどコピーしたURL---
```
例
```shell
git clone https://github.com/y-tamama/PricingAIFrontend.git
```
プロキシを切り忘れるとエラーが出る可能性が高いので注意すること。なお、コマンド入力後にEnterを押し忘れることで実行されないミスもあり得るので、入力するだけでなくEnterも押すこと。
![ターミナルにコマンドを入力する。](../assets/images/init4.png)
---
以上。フォルダ内にコードがコピーされていることを確認する。
