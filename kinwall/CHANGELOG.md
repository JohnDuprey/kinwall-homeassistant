# Changelog

The add-on version is the Kinwall server version it runs (`ghcr.io/johnduprey/kinwall:<version>`).

## 1.4.0

Runs Kinwall 1.4.0.

[Release notes](https://github.com/JohnDuprey/kinwall/releases/tag/v1.4.0) · [All changes since 1.3.0](https://github.com/JohnDuprey/kinwall/compare/v1.3.0...v1.4.0)

#### [1.4.0](https://github.com/JohnDuprey/kinwall/compare/v1.3.0...v1.4.0) (2026-11-15)


##### New

* **board:** put today's status in one strip above the cards ([5045c65](https://github.com/JohnDuprey/kinwall/commit/5045c65920e77f40d64608ac88854cb99c39f116))
* **calendar:** add shared weekly planning ([f626c5e](https://github.com/JohnDuprey/kinwall/commit/f626c5e35fadb50a0f4eb0f5cdd8ac81c9052798))
* **calendar:** allow dismissing the home planner prompt ([9887dc7](https://github.com/JohnDuprey/kinwall/commit/9887dc7f2c4166f72a7bc3f7db40d577ecb19ab9))
* **calendar:** show the event's calendar in its details ([30ee3b6](https://github.com/JohnDuprey/kinwall/commit/30ee3b6a2c1a9bcc93536202377d7aa320579618))
* **chores:** add manual order, categories and ongoing chores ([7b2cdbc](https://github.com/JohnDuprey/kinwall/commit/7b2cdbcfaddd9c6b89470e93a8f9ba4a5d666520)), closes [#94](https://github.com/JohnDuprey/kinwall/issues/94)
* **chores:** assign a chore to several people ([d875ac6](https://github.com/JohnDuprey/kinwall/commit/d875ac6aeee659d64048b1fce264536930c5e63b))
* **chores:** dismiss missed chores without awarding points ([c103492](https://github.com/JohnDuprey/kinwall/commit/c1034920b0690918025f8cd211ff7bc7926fc1df))
* **chores:** open a late chore's checklist on its day ([41785fe](https://github.com/JohnDuprey/kinwall/commit/41785fe58428d1d52f833368a6445bf85e6da6de)), closes [#77](https://github.com/JohnDuprey/kinwall/issues/77)
* **chores:** show a repeating chore's missed last time as late ([fdb4322](https://github.com/JohnDuprey/kinwall/commit/fdb4322d504da1e7781a0f07e8a91d79ef58f9c0)), closes [#77](https://github.com/JohnDuprey/kinwall/issues/77)
* **chores:** show late one-off chores on the board ([dc37c54](https://github.com/JohnDuprey/kinwall/commit/dc37c54d008160e9641bd03a74e605ff2a6eb36b)), closes [#77](https://github.com/JohnDuprey/kinwall/issues/77)
* **inbox:** add a quick-capture inbox for parents ([be71f2b](https://github.com/JohnDuprey/kinwall/commit/be71f2b42f8374f26bc967c27e7e4bf7b6d2fd71))
* **lists:** add pantry lists with use-by dates and meal ideas ([#89](https://github.com/JohnDuprey/kinwall/issues/89)) ([fded338](https://github.com/JohnDuprey/kinwall/commit/fded3380b422ee5291e263a796aac0a204bbffaa))
* **lists:** support barcode scanning in pantry lists ([4082f02](https://github.com/JohnDuprey/kinwall/commit/4082f02cc893b332da8b38eff2794f91578e94e5))
* **recipes:** share selectors and add sorting and cooking filters ([e774848](https://github.com/JohnDuprey/kinwall/commit/e77484837b2377a195226fee8816921167529672))
* **server:** give the android app the address to enroll with ([fcbf5dd](https://github.com/JohnDuprey/kinwall/commit/fcbf5dda13e8da1c67d2113e4f381446f41a9f28)), closes [#77](https://github.com/JohnDuprey/kinwall/issues/77)
* **settings:** say why the app's push notifications are off ([33e4039](https://github.com/JohnDuprey/kinwall/commit/33e403954bd20beeb166ef194a297db2e84e8c15)), closes [#77](https://github.com/JohnDuprey/kinwall/issues/77)


##### Fixed

* **auth:** require user verification in passkey requests ([6e9d77a](https://github.com/JohnDuprey/kinwall/commit/6e9d77a45a6aa192bef19a5676a89e5d41a18c21))
* **board:** fill today at a glance and show it on tablets standing up ([af6107e](https://github.com/JohnDuprey/kinwall/commit/af6107e7aee8c044d5c05425d280d7ac9f00f8d1))
* **board:** fit the board to the room left; chores before approvals on wide screens ([205fb20](https://github.com/JohnDuprey/kinwall/commit/205fb205c13eea321bba9b6e07617d091bf81a1f))
* **board:** keep late chores from being cut off on a tight chores card ([7725a6e](https://github.com/JohnDuprey/kinwall/commit/7725a6e05a5ecc3c4caa2dcea9d8ff1a0dae46b0))
* **board:** keep the scrolling board at its content height ([cbdc03d](https://github.com/JohnDuprey/kinwall/commit/cbdc03d5bb7b225a2c4f84b6d10763bc3769c5ae))
* **board:** stop a card's rows flickering between fit and More ([39c2294](https://github.com/JohnDuprey/kinwall/commit/39c2294e0d9cc67fc676ee85392fa83cd820d1cf))
* **calendar:** fit planner control in the phone toolbar ([c7bb308](https://github.com/JohnDuprey/kinwall/commit/c7bb3085ead92c0bdd7176fe21c4ce31b53ef611))
* **calendar:** keep planning exit controls visible on phones ([44f8e01](https://github.com/JohnDuprey/kinwall/commit/44f8e011e6aa95702427e3c5f8bc07b42d0108af))
* **calendar:** roll today views past midnight, fix races ([cbeb340](https://github.com/JohnDuprey/kinwall/commit/cbeb34041a56430e1f2a2fc27d15a5c5402c99f8))
* **calendar:** say "At the start" for a reminder at the start time ([1dffd58](https://github.com/JohnDuprey/kinwall/commit/1dffd5893799b9e41bec56edb69895b4ca7d1591))
* **calendar:** send event reminders set more than two days ahead ([da63381](https://github.com/JohnDuprey/kinwall/commit/da63381d166e74d869d4ea4e8c6e290a5eb35192))
* **calendar:** show one-day all-day events without a date range ([d561955](https://github.com/JohnDuprey/kinwall/commit/d561955515593532911e0cf5702e6c3c88d2272d))
* **chores:** keep cards readable while ordering in narrow columns ([b8f85f4](https://github.com/JohnDuprey/kinwall/commit/b8f85f40ad7da0a699c19ec54a4ef5e06c96286e))
* **chores:** limit undoing a tick to the days a device can tick ([8ef4e59](https://github.com/JohnDuprey/kinwall/commit/8ef4e599d44a2ca702f0ebaec97f56a0d3996a26))
* **chores:** move repeat and due up, fold advanced options, compact Up and Down ([4ee99ff](https://github.com/JohnDuprey/kinwall/commit/4ee99ff54f01f8fcb0bb083dde40afd1cdb55554))
* **contacts:** save an edited phone number sent with its old value ([ea6e25d](https://github.com/JohnDuprey/kinwall/commit/ea6e25d975a8039a4847ab6421cf3f831b9eddab))
* **inbox:** link what an interrupted sort made instead of making it again ([4e86097](https://github.com/JohnDuprey/kinwall/commit/4e86097fa9adf61f1279bf047be411d1756078e4))
* **lists:** keep a list open after saving its settings ([#91](https://github.com/JohnDuprey/kinwall/issues/91)) ([ce25c0e](https://github.com/JohnDuprey/kinwall/commit/ce25c0efe76f9d04c25a4875399a25f1970b3f7f)), closes [#90](https://github.com/JohnDuprey/kinwall/issues/90)
* **lists:** keep add fields clear of the phone status bar ([54a5bc2](https://github.com/JohnDuprey/kinwall/commit/54a5bc26fb9a071919daf36c9bc136317596c457))
* **lists:** refresh cards when the default list changes ([c580bea](https://github.com/JohnDuprey/kinwall/commit/c580bea96d211fde8aec616fb0294828b7d513d8))
* **mcp:** accept the six redirect addresses gemini registers ([92cea8b](https://github.com/JohnDuprey/kinwall/commit/92cea8bfd41b9d03ec7ad0758cdc7bf1da4b8574))
* **mcp:** read list_events dates as days in the household timezone ([3a20007](https://github.com/JohnDuprey/kinwall/commit/3a2000762414b4fc0fcb7e3de62e45f8aacb0bb3))
* **meals:** leave ingredients already on the list unticked and enlarge check rows ([1533ea3](https://github.com/JohnDuprey/kinwall/commit/1533ea38d3f843b872e34b946fca070e5de9c7e0))
* **meals:** put eating-out order actions on top and drop the duplicate status ([7350ac9](https://github.com/JohnDuprey/kinwall/commit/7350ac9d865fc66bfcefbeee46035c7e239fce8f))
* **meals:** put the step first in cooking mode and read bigger on a wall ([60ce015](https://github.com/JohnDuprey/kinwall/commit/60ce015176ae1a39731f4e82c6a862f82064fad7))
* **meals:** scope the larger check rows to the groceries preview ([bc6fbf7](https://github.com/JohnDuprey/kinwall/commit/bc6fbf77452c878369d2787c411de2502da7b8d1))
* **meals:** show planned meals before Use it up on phones ([438eee2](https://github.com/JohnDuprey/kinwall/commit/438eee2951931fa5a9215a05cf25e1d11b05bc89))
* **recipes:** make "1 hour 15 minutes" one cooking timer ([675cdb2](https://github.com/JohnDuprey/kinwall/commit/675cdb21631571a95206db77d235e682cb4febd5))
* **rewards:** list rewards before milestones and rename the demo milestone ([9f58d8b](https://github.com/JohnDuprey/kinwall/commit/9f58d8b4b71c41bb82ced366f83403babdf7fa9d))
* **server:** keep one push-to-start registration per phone ([cdc471f](https://github.com/JohnDuprey/kinwall/commit/cdc471f85aa31a74375704c49e24843ef4b0fd20))
* **settings:** keep search aliases out of the Inside line ([a89e1d6](https://github.com/JohnDuprey/kinwall/commit/a89e1d68232bd834e42a388dcba90ad964f974c3))
* **sync,chores,plugins,mcp,push,pair:** close feed, race and plugin-id gaps ([f1b1471](https://github.com/JohnDuprey/kinwall/commit/f1b147146d94e0edccc684f8f2be0285515f52d1))
* **sync:** keep all-day feed events on their date in any server timezone ([525071c](https://github.com/JohnDuprey/kinwall/commit/525071c184f65e978a58da06c3fcaf0d3c21308d))
* **sync:** read feed times in the TZID they name without a VTIMEZONE ([792671f](https://github.com/JohnDuprey/kinwall/commit/792671f2799dbfee3aee76c85a0ab97ad3858241))
* **sync:** show feed repeats that started many years ago ([1a067e0](https://github.com/JohnDuprey/kinwall/commit/1a067e0420b2864455b4a8f6e460cfe764df6a50))
* **trackers:** keep coloring pages and profile pictures out of memories ([5090c3b](https://github.com/JohnDuprey/kinwall/commit/5090c3b96b098bcc9fe9f1872956c42907d82b48))
* **web:** align inbox and notification badges ([68a8e1c](https://github.com/JohnDuprey/kinwall/commit/68a8e1c40de55b3e34b4cd4c274014537d50b74e))
* **web:** answer demo chore ticks like the server ([115eb93](https://github.com/JohnDuprey/kinwall/commit/115eb93203aa879e5af031c248ed9d45f12aa7a8))
* **web:** center the Go to Kinwall link on the Authorize error ([840cb33](https://github.com/JohnDuprey/kinwall/commit/840cb3336a5e1d1277905411a144b8da58f3fc61))
* **web:** confirm destructive deletes and plan meals on the viewed day ([48f39ae](https://github.com/JohnDuprey/kinwall/commit/48f39ae67908ac9a51f038222210e4ae9f689829))
* **web:** keep a toast's action on screen when its message is long ([4222c28](https://github.com/JohnDuprey/kinwall/commit/4222c28146fc2cfdc304b863db012bca8c74f2d4))
* **web:** label part-minute timers by how long they run ([7ea38b6](https://github.com/JohnDuprey/kinwall/commit/7ea38b6315694eaba6cf1a525b96dc22f69cf4b0))
* **web:** make interface icons recognizable at small sizes ([de936da](https://github.com/JohnDuprey/kinwall/commit/de936da26b0d54b7c14bcb68e0573122f9e7ed1d))
* **web:** open the demo with just the basics on the board ([461631c](https://github.com/JohnDuprey/kinwall/commit/461631cf027601abb93d8a847ec48a3c4ea40e1d))
* **web:** plain words for chores, meals, settings, passkey errors and MCP text ([8341a89](https://github.com/JohnDuprey/kinwall/commit/8341a8925754bc5c7561d7bc2e975b51a1d03df7))
* **web:** return from free time and journal to their entry points ([089bcd8](https://github.com/JohnDuprey/kinwall/commit/089bcd806f69bfb4f1618c9680a637897a6c6bfb))
* **web:** start new demo recipes blank and keep demo spinach in the fridge ([5e9b209](https://github.com/JohnDuprey/kinwall/commit/5e9b209b7925bec8da40e35f5aac5baf5514d73c))
* **web:** use the local day for demo dates ([ab71a6d](https://github.com/JohnDuprey/kinwall/commit/ab71a6dc362f72db461f8f9bce156dc45086fc1d))
* **web:** validate sign-in URLs and language selection ([68740fc](https://github.com/JohnDuprey/kinwall/commit/68740fc7fd4320adb19a2bb18537a65ab91c8e23))


##### Faster

* **calendar:** read long event reminders through a partial index ([ab0c274](https://github.com/JohnDuprey/kinwall/commit/ab0c27423c18671390ab4938876c7ed569fba06a))
* **meals:** sort pantry once when ranking recipes ([f13c11a](https://github.com/JohnDuprey/kinwall/commit/f13c11a35b828f3305386f0ca62b812eb2be9d12))
* **server:** answer an unchanged native push registration without writing ([470a722](https://github.com/JohnDuprey/kinwall/commit/470a7221ffa468cf384e69b84898adb395b422cd))

## 1.3.0

Runs Kinwall 1.3.0.

[Release notes](https://github.com/JohnDuprey/kinwall/releases/tag/v1.3.0) · [All changes since 1.2.0](https://github.com/JohnDuprey/kinwall/compare/v1.2.0...v1.3.0)

#### [1.3.0](https://github.com/JohnDuprey/kinwall/compare/v1.2.0...v1.3.0) (2026-11-07)


##### ⚠ BREAKING CHANGES

* **chores:** add routine mode screen-time preview
* **upkeep:** tie Done to chore approval and Undo ownership
* **medications:** retry failed gateway medicine alerts
* **push:** add push gateway for self-hosted native push

##### New

* **board:** add scheduled family announcements ([bf2d6da](https://github.com/JohnDuprey/kinwall/commit/bf2d6dab39cd5b6ddffa61033e0d1313762fbe8d))
* **calendar:** follow events with personal Live Activities ([db97d96](https://github.com/JohnDuprey/kinwall/commit/db97d96468e36c6271598ad6e7ecd807f4ffb0f3))
* **calendar:** show overnight events on each spanning day ([450dd48](https://github.com/JohnDuprey/kinwall/commit/450dd4849e385baad9816832bc890909bf289ead)), closes [#50](https://github.com/JohnDuprey/kinwall/issues/50)
* **chores:** add remote app choices for routine mode ([a0f49bb](https://github.com/JohnDuprey/kinwall/commit/a0f49bb3783afa7427eeecdfb1c4172b247a9d6c))
* **chores:** add routine mode screen-time preview ([4906ef2](https://github.com/JohnDuprey/kinwall/commit/4906ef26d34f037b1206da98567299fffe62dceb))
* **chores:** custom repeat schedules and flexible goals ([a9cb002](https://github.com/JohnDuprey/kinwall/commit/a9cb002c7669084b08945ad816e0ea77a90cb93c))
* **chores:** make Anyone chore reminders opt-in ([bb0ff27](https://github.com/JohnDuprey/kinwall/commit/bb0ff2746f2e2854c18607b55d192dcd3d51a989))
* **chores:** match one-time routine requirements by name ([2dbe8d8](https://github.com/JohnDuprey/kinwall/commit/2dbe8d8407a54184701259a8902e87b3d24b042c))
* **chores:** notify devices when a chore is added ([c423675](https://github.com/JohnDuprey/kinwall/commit/c4236757bc794a0b9892e2954e25c6bac12031d8))
* **chores:** show free time status under home chores ([4a2666f](https://github.com/JohnDuprey/kinwall/commit/4a2666f48b0b2839d4335641c21d4fa6ea524cc8))
* **chores:** show unfinished counts on the date strip ([3943648](https://github.com/JohnDuprey/kinwall/commit/39436483a2afbb31b44f436e0c4a87c6d1543318))
* **chores:** support multiple monthly repeat choices ([3c13c01](https://github.com/JohnDuprey/kinwall/commit/3c13c019d2e5ecd1ba9a3f8ada549cf5ad7766d8))
* **chores:** wake child devices after routine changes ([a4e75c4](https://github.com/JohnDuprey/kinwall/commit/a4e75c4cecb3b9c35626e397c74d9d5ffc46b224))
* **lists:** clear ticked grocery and shopping items after a set time ([d6a045a](https://github.com/JohnDuprey/kinwall/commit/d6a045a19546385a9413b63639a84268d317c5b9))
* **medications:** add alarm planning for reminder wakes ([ec09ace](https://github.com/JohnDuprey/kinwall/commit/ec09ace6b4d426350a0debe26d667a03e986972a))
* **medications:** organize medicines around today and history ([8dd33b1](https://github.com/JohnDuprey/kinwall/commit/8dd33b1c1d359d72c2ec700c7b89fc089e9d3f64))
* **medications:** remote Live Activities for medicine doses ([56dd707](https://github.com/JohnDuprey/kinwall/commit/56dd707cc8d35dafd95c3f384a6d3d1263e3f2f4))
* **medications:** retry failed gateway medicine alerts ([0fc7ae3](https://github.com/JohnDuprey/kinwall/commit/0fc7ae32348dc9b6ea0ac4ef717f9a3a03d48d85))
* **outings:** support multi-day visits on calendar add ([9512912](https://github.com/JohnDuprey/kinwall/commit/9512912722a58579ce4c1cb40487fb91519b0220)), closes [#49](https://github.com/JohnDuprey/kinwall/issues/49)
* **push:** add push gateway for self-hosted native push ([582f78b](https://github.com/JohnDuprey/kinwall/commit/582f78b625b41aa4869331d1c3acdc1f5d8e7a0c))
* **push:** native Apple push support ([4fca166](https://github.com/JohnDuprey/kinwall/commit/4fca16644452158739ef373069f57cf4382f4d27))
* **rewards:** add reward milestones ([cdea7de](https://github.com/JohnDuprey/kinwall/commit/cdea7de95078bdae5999582306bd1ff34397f438))
* **server:** add native android fcm push delivery ([d417fc8](https://github.com/JohnDuprey/kinwall/commit/d417fc89a70ae3271a8859d60dd33fdd2e55f725))
* **server:** deliver android alerts through the push gateway ([80c423d](https://github.com/JohnDuprey/kinwall/commit/80c423d6e022fc33773b7e80cb1b3dd2cfdadca3))
* **server:** log rows read by each notification part ([f087fb3](https://github.com/JohnDuprey/kinwall/commit/f087fb3491de6689fafe874a2d81d51f37a311ea))
* **settings:** add optional morning check-in reminders ([cf2bf33](https://github.com/JohnDuprey/kinwall/commit/cf2bf33267b2c4842dbf7e0e73978abde65c2e06))
* **settings:** add status bar visibility toggle for mobile apps ([1317eec](https://github.com/JohnDuprey/kinwall/commit/1317eec8c703fcc9d4969a98e4a2a43be6bb5f1d))
* **settings:** rename paired devices and API keys ([6efa2ef](https://github.com/JohnDuprey/kinwall/commit/6efa2ef26fe4f9f3f3d7c0862b46687d52394493))
* **settings:** support per-device routine unenrollment ([f85d047](https://github.com/JohnDuprey/kinwall/commit/f85d04749372ab8977eba4ab2975c668e48cf266))
* **trackers:** coordinate Open Library requests with a shared client ([927710f](https://github.com/JohnDuprey/kinwall/commit/927710fc73357e909ee7a0cdd4b0e3388de05ff4))
* **upkeep:** add home upkeep with jobs, things, history and reminders ([17107d8](https://github.com/JohnDuprey/kinwall/commit/17107d8532e7e139bf4e5d8930df26e324c61adf))
* **upkeep:** tie Done to chore approval and Undo ownership ([b54d792](https://github.com/JohnDuprey/kinwall/commit/b54d792e3916afe4c3eb387b0762f2ddfa21bfda))
* **web:** sync timer controls with iphone live activities ([af14254](https://github.com/JohnDuprey/kinwall/commit/af1425494304e140204660949e0864e5a5a87aaf))


##### Fixed

* **activities:** finish confirmed exits after dialog dismissal ([b0b0291](https://github.com/JohnDuprey/kinwall/commit/b0b02918da525557b7a7e4c7aa8ab0e53a80d417))
* **auth:** preserve personal identity for watch keys ([1c96ef2](https://github.com/JohnDuprey/kinwall/commit/1c96ef2eeec149895f69f0ee4b4e95360e594463))
* **board:** stabilize nest hub two-column layout ([eabb58b](https://github.com/JohnDuprey/kinwall/commit/eabb58bb39466f7cf943dd411f21c1f22db06fdb))
* **board:** wrap routine status labels at larger text sizes ([7e99b0e](https://github.com/JohnDuprey/kinwall/commit/7e99b0eab699a3b344a6bece284ed7a7694d62c0))
* **build:** include routine website module in docker image ([20bcbbd](https://github.com/JohnDuprey/kinwall/commit/20bcbbdebd2c10ae41f5094de079cc0b3a8ac133))
* **calendar:** prevent duplicate event activity starts ([ddefe9f](https://github.com/JohnDuprey/kinwall/commit/ddefe9f2d660036452b252373acd058bd72b0863))
* **chores:** clarify routine mode status without app choices ([b5e0ad8](https://github.com/JohnDuprey/kinwall/commit/b5e0ad85ec1634a564b83953684cebb658478ce8))
* **chores:** preserve named requirements for older child apps ([da3e246](https://github.com/JohnDuprey/kinwall/commit/da3e246254a41f21f72f8a310b78142cc9b8da66))
* **chores:** read a child's routine chores through an index ([4a98e53](https://github.com/JohnDuprey/kinwall/commit/4a98e534276e3aeb4d9310791f108523c319bef0))
* **chores:** space free time controls consistently ([bbf8e60](https://github.com/JohnDuprey/kinwall/commit/bbf8e60e2dc25c3423fdff2cf93ad7c399540844))
* **medications:** clear live activities on all subscribed devices ([39d37fe](https://github.com/JohnDuprey/kinwall/commit/39d37fef6469d5dd25c424984968811af8cda8a0))
* **outings:** close an outing's sheet for good ([#54](https://github.com/JohnDuprey/kinwall/issues/54)) ([48ddfbc](https://github.com/JohnDuprey/kinwall/commit/48ddfbc00ee4a0c33495366bca859f847e39011b))
* **push-gateway:** avoid redirect:error in gateway fetch ([71c0844](https://github.com/JohnDuprey/kinwall/commit/71c0844065cf0f367ae246a5191592d734eb76e7))
* **server:** avoid broken pipes when checking test summaries ([353b66c](https://github.com/JohnDuprey/kinwall/commit/353b66c9e8d15d09c868a7b30e47525a1519135a))
* **server:** honor saved public URL for push gateway ([0b2cfc8](https://github.com/JohnDuprey/kinwall/commit/0b2cfc848f4b8b71163ba669b4ea77958d78ab83))
* **server:** isolate android gateway cleanup and readiness ([8725893](https://github.com/JohnDuprey/kinwall/commit/8725893d2ef1cc51bb27418b42d336521be76b2e))
* **server:** keep android alerts for an hour so sleeping devices get them ([73a3ede](https://github.com/JohnDuprey/kinwall/commit/73a3ede01bb964de1f8badd7344410b1300e421b))
* **server:** read only the rows frequent queries need ([ced576c](https://github.com/JohnDuprey/kinwall/commit/ced576cc6fbb5f4310581b7e493b4797ab475618))
* **settings:** explain child device setup and contain routine layout ([c72de62](https://github.com/JohnDuprey/kinwall/commit/c72de62f7048ba32b541da0f5a976b8c337eeaf3))
* **settings:** preserve routine choices and finish device setup ([f8f1600](https://github.com/JohnDuprey/kinwall/commit/f8f1600ae86ebf019fad4fa22111500564f78813))
* **trackers:** use workers-compatible redirect handling ([6bf3179](https://github.com/JohnDuprey/kinwall/commit/6bf3179eba57e32de0468e60fa365bcbf8fb5abe))
* **web:** fit navigation to the available rail height ([d343500](https://github.com/JohnDuprey/kinwall/commit/d3435003001f44809b082a1ac994a2f98b2c96c2))
* **web:** restore nooks as the English heading ([bc78850](https://github.com/JohnDuprey/kinwall/commit/bc78850979559a00948917be608c37c03137d195))


##### Faster

* **board:** keep card fit observers attached across renders ([a7c1c53](https://github.com/JohnDuprey/kinwall/commit/a7c1c53c2734bfbc21262e092502996f95d43e4a))
* **board:** skip idle routine status requests ([c809e4c](https://github.com/JohnDuprey/kinwall/commit/c809e4cdd316f324e195914bae46457506303a21))
* **board:** stop polling announcements every 30 seconds ([7e67e7b](https://github.com/JohnDuprey/kinwall/commit/7e67e7bb1ca886f85bbd746de11aca416eecb661))
* **calendar:** limit related reads to matching events ([e849d0c](https://github.com/JohnDuprey/kinwall/commit/e849d0cb794821825530d00b548ce99b8637ddb7))
* **recipes:** use indexed lookups for a single recipe ([a49ad8e](https://github.com/JohnDuprey/kinwall/commit/a49ad8eeed74df78995d1751113d2020876efecd))
* **server:** read lists, the feed and active chores without scanning history ([ebba498](https://github.com/JohnDuprey/kinwall/commit/ebba498d718022ed690c1a3f3837a7d03818a0ca))
* **server:** read today's and this week's points from daily totals ([66333ec](https://github.com/JohnDuprey/kinwall/commit/66333eca5197f40ab189ac473bbe1627c8feacf0))
* **server:** reduce medicine and core refresh reads ([4788ec6](https://github.com/JohnDuprey/kinwall/commit/4788ec6e5e38def64c9fa59a39668faedc3213c2))
* **server:** reuse daily summary reads across recipients ([72494b2](https://github.com/JohnDuprey/kinwall/commit/72494b271473242089e302d22bc4fdf1585492fd))
* **web:** load secondary screens after startup ([57e79bd](https://github.com/JohnDuprey/kinwall/commit/57e79bd527da9cbef13f8b92ccfd261d0bb401ac))


##### Chores

* release 1.3.0 ([7ac8135](https://github.com/JohnDuprey/kinwall/commit/7ac81359b07ea57e268ed39400353e0f979a9189))

## 1.2.0

Runs Kinwall 1.2.0: connected to-do apps, family polls, outings, restaurant menus and orders,
German, and an easier-to-use calendar, Board and chore chart.

### Calendar and wall screens

- **Calendar has its own place** beside Home, with Day, Week, Month and Schedule views (3 Day on
  phones). Home holds Board and Newscast; find Board layouts and category filters under
  **Layout and filter** on its toolbar.
- Today's events put what's on now and next first. Meal events show whether dinner is cooked or
  ordered, and how many people have ordered. Events synced from two calendars appear once on
  the Board.
- Pick a default calendar and event length, and repeat an event yearly.
- Better layouts and text sizes on phones, tablets and wall screens, with a screen scale setting
  and a cast screen mode for smart displays.
- Picking someone on a shared wall remembers who's using it until it goes idle, so chores,
  votes and activities need fewer taps.

### Lists and shopping

- **Two-way to-do sync** with Todoist, Google Tasks and Microsoft To Do, including titles,
  completion, due dates, notes and checklist steps. Priority syncs where the app supports it.
  Connect under **Settings → Calendars → To-do apps**, then choose **Edit → Sync with…** on a
  to-do list. Changes in Kinwall go out within seconds; changes in the other app are checked
  about every two minutes. Parents see warnings and get notified if a sign-in stops working.
- **Get stuff done** walks through a checklist, including a chore's steps. Add its progress card
  to the Board or pin a checklist to a screen.
- Mark who an item is for. Shopping lists gain an add-item sheet, an on-sale flag, default stores
  for Groceries and Shopping, and easier aisle ordering.
- Shopping mode remembers where you found things, warns when a scanned item is already on the
  list, and offers Undo when you end a trip. Barcode matching and department grouping are fixed.

### Meals, polls and outings

- **Restaurants**: keep menus and family favorites together, import menus from links or photos,
  and collect everyone's order for pickup, delivery or eating out.
- **Family polls**: vote on plans, see the leading choice, pick a restaurant from the binder,
  and turn the result into a calendar event. Open polls appear on the Board.
- **Outings**: save things to do and places to go, mark interest, set reminders, and import ideas
  from links, flyers, maps and community calendars.
- Favorite recipes for each person. Cooking mode keeps instructions in view, and timers for
  ranges such as 15–20 minutes give a check chime before the final ring.

### Chores, rewards and family

- **Edit chores** and **Edit lists** replace press and hold on parent devices.
- Kids can suggest a chore for a parent to approve. Parents can give bonus points outside a
  chore, and chores can have a start time and timer.
- Activity chores count time while a kid is actually playing and show progress. Checklist chores
  finish when the last step is ticked, and points and leaderboards refresh correctly.
- Split a reward between several people and open a person's points history from their balance.
- Medicine refill cards help arrange a refill and track it with a to-do. Parents can see kids'
  due doses on their phone and correct a dose's recorded time or status.
- Turn a calendar event into a health visit, and log or correct reading for an earlier day.
- The library gains cover and shelf views, separate audiobook entries, richer book details,
  and more filters and sorting.
- Profile pictures can come from a photo, drawing or camera. Paint gains a pencil, more coloring
  pages, zoom and pan.

### Language and everyday improvements

- **German** across Kinwall's screens, reminders, notifications and other server-written text.
  Choose a family language and an optional language for each person. Thanks to
  [sudo-Foras666](https://github.com/sudo-Foras666) for the translation.
- Search across Settings, jump straight to help for the current page, and find advanced access
  settings together.
- Back closes the current sheet or full-screen mode. Unsaved forms ask before discarding changes.
  Larger touch targets, clearer errors with Try again, and better keyboard and landscape layouts.
- Security fixes strengthen sign-in refreshes, activity plugins, shared-content parsing and
  photo previews.

### Upgrading from 1.1.0

- Back up the Home Assistant app before updating, including its persistent data and encryption
  key. Database migrations run automatically at startup. Reload open Kinwall screens afterward;
  if a device keeps showing the old version, use **Settings → General → Troubleshooting →
  Clear cache and reload** in Kinwall.
- **Meal status change for API and MCP users:** `handled` is no longer accepted. Send `prepared`
  for Cooked or Ordered, or `planned`. Existing `handled` meals are converted automatically.
- Google Tasks and Microsoft To Do need the corresponding Google or Microsoft sign-in provider
  configured and a new tasks permission grant. The app's `public_url` is needed for those OAuth
  redirects. Todoist connects with an API token.
- Keep the separate **Kinwall HACS integration at 1.9.0 or later**, as with app 1.1.0. This app
  update runs the Kinwall server; the HACS integration is updated separately.

## 1.1.0

- Runs Kinwall 1.1.0: the Board, meals and recipes, groceries in store order, rewards, medicines, check-ins, Newscast, a family library, Peacock as the default look and a new logo, plus many fixes. See the [release notes](https://github.com/JohnDuprey/kinwall/releases/tag/v1.1.0), and read their Upgrading section first.
- Passkeys work at the address Home Assistant serves the app on (`public_url` is only needed for Google or Microsoft sign-in).
- New app icon and logo.
- Pair it with the Kinwall integration 1.9.0 or later.

## 1.0.3

- Fixed: adding a passkey failed with "Unexpected registration response origin" when Home Assistant serves https itself (for example on port 8443). Kinwall now accepts the https address of the host the request came in on.

## 1.0.2

- Fixed: the add-on could not start because `/data` is mounted root-owned and the server runs as an unprivileged user (`EACCES` on `/data/encryption.key`). The container now makes `/data` writable, then drops privileges.

## 1.0.1

- Fixed: the Kinwall integration's push webhook was refused (Home Assistant's internal URL is a LAN address). The add-on now runs with `ALLOW_PRIVATE_WEBHOOK_URLS=1`, so push updates work out of the box.
- Fixed: the `microsoft_client_id` / `microsoft_client_secret` options never reached the server.

## 1.0.0

- First release: Kinwall server as a Home Assistant add-on with ingress, optional direct LAN port for a kiosk iPad, and Google / Microsoft OAuth options.
