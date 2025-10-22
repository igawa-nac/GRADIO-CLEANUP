# databricks Apps上での環境変数の利用方法(機密情報について)

いわゆるシークレットの扱い方についてまとめます。

## シークレットの設定方法
基本的には[このドキュメント](https://learn.microsoft.com/ja-jp/azure/databricks/security/secrets/)に従えば問題ないのですが、PowerShellだと上記ドキュメントではうまくいかなかったのでいかに手法を載せます。

### スコープについて
databricksのシークレットは、スコープという権限的区切りがあり、その中にキーと値のセットがあるような形式です。
今回はpricing-frontendというスコープを利用しようと思います。新規作成したい場合は上記ドキュメントを確認してください。

### シークレットをセットする
以下のようなコマンドを実行すると文字列のシークレットを設定できます。
```shell
databricks secrets put-secret pricing-frontend KEYNAME --string-value "ここに値を入力します。"
```

### シークレットをCLIで確認する
セットしたシークレットをPowerShellなどのコマンドで確認する場合、デコードをする必要があるので少し複雑になります。(databricks Apps上で利用する際はデコードする必要はありません。)
```shell
$response = databricks secrets get-secret pricing-frontend KEYNAME
$json = $response | ConvertFrom-Json
$decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($json.value))
Write-Output $decoded
```


### シークレットをdatabricks上で利用する
GradioなどのPythonを用いてdatabricks上でシークレットを利用するには、まずアプリに対してシークレットの利用を許可する必要があります。

1. アプリのデプロイページの編集ボタンをクリックします。
![アプリのデプロイページの編集ボタンをクリック](../assets/images/usesecret1.png)

2. 「次のページ」をクリックして、「リソースの追加」をクリックします。プルダウンについては「シークレット」を選択します。
![リソースを追加をクリック](../assets/images/usesecret2.png)

3. 以下のような画面において、「範囲」はスコープ名(pricing-frontend)、範囲を選んだら出てくるプルダウンには利用するシークレットキー名、権限は「読み取り可」など、リソースキーはアプリに渡すときに利用する名前(おすすめはシークレットキー名のままか、スコープ名+シークレットキー名など)を入力する。設定したら「保存」ボタンをクリックすることを忘れずに。
![シークレット](../assets/images/usesecret3.png)

これでアプリがシークレットへのアクセス権限を得ることができました。

次に、アプリ内のPythonコードでシークレットを取得します。
1. ルートディレクトリにapp.yamlがなければ作成して、以下の内容を追記します。
```yaml
env:
  - name: 'シークレットネーム'  # Pythonコード内で利用する時の名前。リソースキー名と同じで基本は問題ない。
    valueFrom: 'ResourceKey'  # 設定したリソースキー名
```

2. Pythonコードで以下のコードを追記します。
```python
import os
secret_value = os.getenv('シークレットネーム') # app.yamlで設定した内容に変える。
```
するとsecret_valueにシークレットにおいて設定した値が入ります。
