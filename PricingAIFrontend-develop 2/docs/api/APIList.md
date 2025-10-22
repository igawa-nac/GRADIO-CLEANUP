# API一覧(フロントエンド向け)
## databricks URLについて
以下のAPI表で提示するパス(URLの一部)は、すべて**Azureに展開されているdatabricksワークスペースURL**の続きとしてのものです。

databricksワークスペースURLは、 **https://adb-46569xxxxxxxxxxx.xx.azuredatabricks.net** みたいな形式です。

例えば、 **/user/list/** というのが示されていたら、 **https://adb-46569xxxxxxxxxxx.xx.azuredatabricks.net/user/list/** としてフロントエンドに実装します。

それでは、以下が一覧になります。

## /api/2.2/jobs/run-now
- POST
- 認証必須
- json : {"job_id", ...}
- response: {"run_id", ...}
Jobsを開始させます。開始されたJobからrun_idを返されます。

## /api/2.2/jobs/runs/get/
- GET
- 認証必須
- json {"run_id"}
- response : {"state" : {"life_cycle_state", ...}, "tasks" : [ {"run_id", ...} ], ...}
現在のrunの実行状況を取得するとともに、タスクのrun_idを取得できます。出力の取得にはrun_idが必要です。

## /api/2.2/jobs/runs/get-output/
- GET
- 認証必要
- json : {"run_id"} //このrun_idはタスクのrun_id
- response : {"notebook_output" : {"result", ...}, ...}
runの出力結果を取得します。

