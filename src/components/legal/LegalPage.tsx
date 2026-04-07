/**
 * 法的情報ページ
 * データ利用・著作権・免責事項を表示する。
 * テキストはユーザー指定の正確な日本語をそのまま使用。
 */

interface LegalPageProps {
  onBack: () => void
}

export function LegalPage({ onBack }: LegalPageProps) {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* 戻るボタン */}
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm text-brand-700 hover:text-brand-900 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        ダッシュボードに戻る
      </button>

      {/* ページタイトル */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">データ利用・著作権・免責事項</h1>
        <p className="text-sm text-gray-500 mt-1">最終更新：2026年4月</p>
      </div>

      {/* リード文 */}
      <p className="text-sm text-gray-700 leading-relaxed">
        本サービス（価格トラッカー）は、複数の外部データソースから価格情報を収集・表示しています。本ページでは、各データソースの利用根拠、法的位置づけ、および免責事項を明示します。
      </p>

      {/* セクション1：データソースと利用根拠 */}
      <Section number="1" title="データソースと利用根拠">
        {/* 1-1 World Bank API */}
        <SourceBlock title="1-1 World Bank API">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="銅、アルミニウム、亜鉛、ニッケル、鉛、錫、鉄鉱石" />
            <DlRow label="ライセンス" value="Creative Commons Attribution 4.0 International (CC BY 4.0)" />
            <DlRow label="商用利用" value="可能 / 出典表示義務：あり" />
            <DlRow label="データURL">
              <ExtLink href="https://api.worldbank.org/v2/">https://api.worldbank.org/v2/</ExtLink>
            </DlRow>
          </dl>
          <p className="text-sm text-gray-600 mt-2">
            CC BY 4.0ライセンスは、出典を明示することを条件に、データの複製・配布・改変・商業利用を広く許諾します。
          </p>
        </SourceBlock>

        {/* 1-2 EIA API */}
        <SourceBlock title="1-2 EIA API（米国エネルギー情報局）">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="原油（WTI）" />
            <DlRow label="法的位置づけ" value="米国連邦政府機関が提供する政府公開データ" />
            <DlRow label="利用制限" value="なし（APIキー登録のみ必要）/ 商用利用：可能" />
            <DlRow label="データURL">
              <ExtLink href="https://api.eia.gov/">https://api.eia.gov/</ExtLink>
            </DlRow>
          </dl>
          <p className="text-sm text-gray-600 mt-2">
            米国政府が作成した著作物は、原則として著作権の保護を受けない（米国著作権法第105条）。本APIデータはパブリックドメイン相当として自由に利用可能です。
          </p>
        </SourceBlock>

        {/* 1-3 日本銀行 */}
        <SourceBlock title="1-3 日本銀行 時系列統計データ検索サイト">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="エチレン、プロピレン、ベンゼン（石油化学基礎製品）、電気銅、鉄筋棒鋼、H形鋼、ステンレス鋼板等（企業物価指数）" />
            <DlRow label="提供元" value="日本銀行（Bank of Japan）" />
            <DlRow label="法的位置づけ" value="日本銀行が公式APIとして提供する統計データ。統計データの利用は自由（日本銀行利用規約より）。出典表示義務あり。" />
            <DlRow label="データURL">
              <ExtLink href="https://www.stat-search.boj.or.jp/">https://www.stat-search.boj.or.jp/</ExtLink>
            </DlRow>
          </dl>
        </SourceBlock>

        {/* 1-4 e-Stat */}
        <SourceBlock title="1-4 e-Stat / 資源エネルギー庁">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="ナフサ輸入価格" />
            <DlRow label="提供元" value="経済産業省 資源エネルギー庁" />
            <DlRow label="法的位置づけ" value="政府統計データ（統計法に基づく基幹統計）。e-Stat利用規約に基づき、出典表示を条件として自由に利用可能。" />
            <DlRow label="データURL">
              <ExtLink href="https://api.e-stat.go.jp/">https://api.e-stat.go.jp/</ExtLink>
            </DlRow>
          </dl>
        </SourceBlock>

        {/* 1-5 日本鉄リサイクル工業会 */}
        <SourceBlock title="1-5 一般社団法人 日本鉄リサイクル工業会">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="鉄スクラップ（H2・HS・H1・シュレッダー等）流通価格" />
            <DlRow label="データURL">
              <ExtLink href="https://www.jisri.or.jp/kakaku">https://www.jisri.or.jp/kakaku</ExtLink>
            </DlRow>
            <DlRow label="取得方法" value="HTMLスクレイピング（月1回以内）" />
            <DlRow label="robots.txt" value="/kakakuページへのアクセス禁止の記述なし（確認済）" />
            <DlRow label="利用規約" value="サイト上に利用規約・禁止事項の記載なし（確認済）" />
            <DlRow label="著作権の観点" value="収集対象は「価格」という事実情報であり、著作物性が低い" />
            <DlRow label="アクセス管理" value="月1回以内、User-Agentに識別情報を明記" />
          </dl>
        </SourceBlock>

        {/* 1-6 東京製鐵 */}
        <SourceBlock title="1-6 東京製鐵株式会社">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="鉄スクラップ購入価格（特級・H2等）、鋼材販売価格（熱延コイル、冷延コイル、H形鋼、異形棒鋼、厚板等）" />
            <DlRow label="データURL（スクラップ）">
              <ExtLink href="https://www.tokyosteel.co.jp/scrapprice/">https://www.tokyosteel.co.jp/scrapprice/</ExtLink>
            </DlRow>
            <DlRow label="データURL（鋼材）">
              <ExtLink href="https://www.tokyosteel.co.jp/salesprice/">https://www.tokyosteel.co.jp/salesprice/</ExtLink>
            </DlRow>
            <DlRow label="取得方法" value="HTMLスクレイピング（月1回以内）" />
            <DlRow label="robots.txt" value="存在しない（404）＝クロール禁止の記述なし（確認済）" />
            <DlRow label="利用規約ページ" value="存在しない（404）＝スクレイピング禁止条項なし（確認済）" />
            <DlRow label="アクセス管理" value="月1回以内、User-Agentに識別情報を明記" />
          </dl>
        </SourceBlock>

        {/* 1-7 日本鉄源協会 */}
        <SourceBlock title="1-7 一般社団法人 日本鉄源協会">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="鉄スクラップ（H2炉前価格 三地区平均、1987年度〜）" />
            <DlRow label="データURL">
              <ExtLink href="http://tetsugen.or.jp/kiso/2sukurap.htm">http://tetsugen.or.jp/kiso/2sukurap.htm</ExtLink>
            </DlRow>
            <DlRow label="法的位置づけ" value="一般社団法人日本鉄源協会が公表する業界統計" />
            <DlRow label="利用条件" value="非商用の情報収集・参考目的での参照。データは参考値として表示し、同協会が公表する数値であることを明示" />
          </dl>
        </SourceBlock>

        {/* 1-8 Westmetall */}
        <SourceBlock title="1-8 Westmetall">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="LMEニッケル（現物）、LME錫（現物）" />
            <DlRow label="データURL">
              <ExtLink href="https://www.westmetall.com/en/markdaten.php">https://www.westmetall.com/en/markdaten.php</ExtLink>
            </DlRow>
            <DlRow label="法的位置づけ" value="ドイツの民間金属情報サービスが整理・公表するLME市場価格データ" />
            <DlRow label="利用条件" value="本サービスでは価格の数値のみを非商用目的で参照し、データは参考値として表示" />
          </dl>
        </SourceBlock>

        {/* 1-9 日本銀行 企業物価指数（CGPI） */}
        <SourceBlock title="1-9 日本銀行 企業物価指数（CGPI）">
          <dl className="space-y-1">
            <DlRow label="対象品目" value="特殊鋼・ステンレス（物価指数、2020年=100）" />
            <DlRow label="データURL">
              <ExtLink href="https://www.boj.or.jp/statistics/pi/cgpi_2020/index.htm">https://www.boj.or.jp/statistics/pi/cgpi_2020/index.htm</ExtLink>
            </DlRow>
            <DlRow label="法的位置づけ" value="日本銀行が公表する公的統計データ" />
            <DlRow label="利用条件" value="出典を明示することで利用可能" />
          </dl>
          <p className="text-sm text-amber-700 font-medium mt-2">
            重要: このデータは2020年を100とした物価指数であり、円/トンの実際の取引価格ではありません。
          </p>
        </SourceBlock>
      </Section>

      {/* セクション2：データ収集の法的根拠 */}
      <Section number="2" title="データ収集の法的根拠">
        {/* 2-1 著作権法 */}
        <LegalBlock title="2-1 著作権法（著作権侵害の非該当性）">
          <p className="text-sm text-gray-700 leading-relaxed">
            著作権法（昭和45年法律第48号）は、「思想または感情を創作的に表現したもの」（第2条第1項第1号）のみを保護対象とします。本サービスが収集するのは商品・資源の「市場価格」という事実情報であり、以下の理由から著作物性が認められません：
          </p>
          <ol className="list-decimal list-inside text-sm text-gray-700 mt-2 space-y-1 ml-2">
            <li>価格は客観的な市場の事実であり、創作性を含まない。</li>
            <li>数値データ（○○円/トン）それ自体は表現ではなく事実。</li>
            <li>日本の裁判例においても、単純な数値データには著作物性が否定される傾向にある。</li>
          </ol>
        </LegalBlock>

        {/* 2-2 不正競争防止法 */}
        <LegalBlock title="2-2 不正競争防止法（データベース保護の非該当性）">
          <p className="text-sm text-gray-700 leading-relaxed">
            不正競争防止法（平成5年法律第47号）第2条第1項第11号は、「限定提供データ」の不正取得を規制しています。しかし、本サービスが収集するデータはいずれも一般に公開されたデータであり、「限定提供データ」（アクセス制限を設けて特定の者に限り提供されるデータ）には該当しません。
          </p>
        </LegalBlock>

        {/* 2-3 不法行為法 */}
        <LegalBlock title="2-3 不法行為法（業務妨害の非該当性）">
          <p className="text-sm text-gray-700 leading-relaxed">
            民法第709条に基づく不法行為（業務妨害）は、過度なアクセスによりサーバーに負荷をかける行為が問題となります。本サービスでは以下の対策を講じており、業務妨害に当たらないと判断しています：
          </p>
          <ol className="list-decimal list-inside text-sm text-gray-700 mt-2 space-y-1 ml-2">
            <li>アクセス頻度の制限：月1回以内（通常の閲覧頻度の範囲内）。</li>
            <li>User-Agentの明示：PriceTracker/1.0を含む識別情報を付与。</li>
            <li>robots.txtの遵守：各サイトのrobots.txtを確認・遵守。</li>
            <li>対象ページの限定：価格情報ページのみを対象。</li>
          </ol>
        </LegalBlock>

        {/* 2-4 コンピュータ不正アクセス禁止法 */}
        <LegalBlock title="2-4 コンピュータ不正アクセス禁止法（非該当）">
          <p className="text-sm text-gray-700 leading-relaxed">
            不正アクセス行為の禁止等に関する法律（平成11年法律第128号）は、認証機構を回避したアクセスを規制します。本サービスが収集するデータはすべて認証不要の公開ページから取得しており、同法の適用はありません。
          </p>
        </LegalBlock>
      </Section>

      {/* セクション3：免責事項 */}
      <Section number="3" title="免責事項">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 space-y-4">
          <DisclaimerItem title="3-1 データの正確性">
            本サービスが表示する価格情報は各データソースから収集したものですが、データソース側の公表遅延・修正・訂正、収集処理における技術的エラー、スクレイピング対象サイトのHTML構造変更、通信障害その他の不可抗力により、表示内容の正確性・完全性を保証するものではありません。
          </DisclaimerItem>
          <DisclaimerItem title="3-2 利用目的の制限">
            本サービスが提供するデータは参考情報として提供するものであり、株式・商品先物・FX等の投資判断の根拠として使用した場合、商業取引における売買価格の根拠として使用した場合、その他の経営・財務上の意思決定に使用した場合について、当サービスは一切の責任を負いません。投資・商業判断を行う際は、必ず一次情報源および専門家の助言を確認してください。
          </DisclaimerItem>
          <DisclaimerItem title="3-3 データ更新の停止">
            データソース側のサイト構造変更、API仕様変更、サービス終了等により、特定のデータソースからの情報収集が停止する場合があります。その場合、該当品目のデータが更新されないことがあります。当サービスはこれによる損害について責任を負いません。
          </DisclaimerItem>
        </div>
      </Section>

      {/* セクション4：出典・帰属表示 */}
      <Section number="4" title="出典・帰属表示（Attribution）">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">データ</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">提供元</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">ライセンス</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <AttrRow data="銅・アルミ・亜鉛・ニッケル・鉛・錫・鉄鉱石 価格" provider="World Bank Group" license="CC BY 4.0" />
              <AttrRow data="原油（WTI）価格" provider="U.S. Energy Information Administration (EIA)" license="U.S. Government Open Data" />
              <AttrRow data="企業物価指数（エチレン・プロピレン・ベンゼン・鉄鋼・非鉄）" provider="日本銀行" license="統計データ自由利用" />
              <AttrRow data="ナフサ輸入価格" provider="経済産業省 資源エネルギー庁（e-Stat提供）" license="政府統計データ" />
              <AttrRow data="鉄スクラップ流通価格" provider="一般社団法人 日本鉄リサイクル工業会" license="一般公開データ" />
              <AttrRow data="鉄スクラップ購入価格・鋼材販売価格" provider="東京製鐵株式会社" license="一般公開データ" />
            </tbody>
          </table>
        </div>

        {/* 著作権表示文 */}
        <div className="mt-4 space-y-1 text-xs text-gray-500 bg-gray-50 rounded-lg p-4">
          <p className="font-semibold text-gray-600 mb-2">著作権表示文：</p>
          <p>&copy; World Bank Group. Licensed under CC BY 4.0. <ExtLink href="https://www.worldbank.org/">https://www.worldbank.org/</ExtLink></p>
          <p>U.S. Energy Information Administration (EIA). Public domain. <ExtLink href="https://www.eia.gov/">https://www.eia.gov/</ExtLink></p>
          <p>&copy; Bank of Japan. <ExtLink href="https://www.boj.or.jp/">https://www.boj.or.jp/</ExtLink></p>
          <p>&copy; 総務省統計局 / 経済産業省 資源エネルギー庁. <ExtLink href="https://www.e-stat.go.jp/">https://www.e-stat.go.jp/</ExtLink></p>
          <p>&copy; 一般社団法人 日本鉄リサイクル工業会. <ExtLink href="https://www.jisri.or.jp/">https://www.jisri.or.jp/</ExtLink></p>
          <p>&copy; 東京製鐵株式会社. <ExtLink href="https://www.tokyosteel.co.jp/">https://www.tokyosteel.co.jp/</ExtLink></p>
        </div>
      </Section>

      {/* セクション5：データ更新頻度 */}
      <Section number="5" title="データ更新頻度">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">データソース</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">対象品目</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">更新頻度</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">更新タイミング</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <FreqRow source="World Bank API" items="銅・アルミ・亜鉛・ニッケル・鉛・錫・鉄鉱石" freq="月次" timing="毎週月曜日（自動）" />
              <FreqRow source="EIA API" items="原油（WTI）" freq="週次" timing="毎週月曜日（自動）" />
              <FreqRow source="日本銀行 CGPI" items="エチレン・プロピレン・ベンゼン・電気銅・鉄鋼指数" freq="月次" timing="毎週月曜日（自動）" />
              <FreqRow source="e-Stat / 資源エネルギー庁" items="ナフサ輸入価格" freq="月次" timing="毎週月曜日（自動）" />
              <FreqRow source="日本鉄リサイクル工業会" items="鉄スクラップ流通価格" freq="月次" timing="手動更新ボタン" />
              <FreqRow source="東京製鐵" items="鉄スクラップ購入価格・鋼材販売価格" freq="月次" timing="手動更新ボタン" />
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          注記：手動更新ボタンは画面上部の「データを更新」ボタンを押した際に取得します。自動更新は毎週月曜日の深夜（日本時間）に実行されます。
        </p>
      </Section>
    </div>
  )
}

/* --- サブコンポーネント --- */

function Section({ number, title, children }: { number: string; title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-bold text-gray-800 mb-4">
        <span className="text-brand-600 mr-1">{number}.</span>
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </section>
  )
}

function SourceBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-gray-100 rounded-lg p-4">
      <h3 className="text-sm font-bold text-gray-700 mb-2">{title}</h3>
      {children}
    </div>
  )
}

function LegalBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-l-4 border-brand-200 pl-4 py-1">
      <h3 className="text-sm font-bold text-gray-700 mb-2">{title}</h3>
      {children}
    </div>
  )
}

function DlRow({ label, value, children }: { label: string; value?: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:gap-2 text-sm">
      <dt className="font-medium text-gray-600 sm:w-40 flex-shrink-0">{label}：</dt>
      <dd className="text-gray-800">{children ?? value}</dd>
    </div>
  )
}

function DisclaimerItem({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-sm font-semibold text-amber-800">{title}</p>
      <p className="text-sm text-amber-700 mt-0.5 leading-relaxed">{children}</p>
    </div>
  )
}

function AttrRow({ data, provider, license }: { data: string; provider: string; license: string }) {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-2.5 text-gray-800">{data}</td>
      <td className="px-4 py-2.5 font-medium text-gray-700">{provider}</td>
      <td className="px-4 py-2.5">
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{license}</span>
      </td>
    </tr>
  )
}

function FreqRow({ source, items, freq, timing }: { source: string; items: string; freq: string; timing: string }) {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-2.5 font-medium text-gray-800">{source}</td>
      <td className="px-4 py-2.5 text-gray-600">{items}</td>
      <td className="px-4 py-2.5 text-gray-600">{freq}</td>
      <td className="px-4 py-2.5 text-gray-600">{timing}</td>
    </tr>
  )
}

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-brand-600 hover:text-brand-800 hover:underline">
      {children}
    </a>
  )
}
