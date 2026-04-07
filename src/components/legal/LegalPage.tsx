/**
 * 法的情報ページ
 * スクレイピングの法的根拠、免責事項、出典表示、データ更新頻度を表示する。
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

      <h1 className="text-2xl font-bold text-gray-900">
        法的情報・データポリシー
        <span className="block text-base font-normal text-gray-500 mt-1">Legal Information &amp; Data Policy</span>
      </h1>

      {/* データソース一覧 */}
      <Section title="データソース" titleEn="Data Sources">
        <p className="text-sm text-gray-600 mb-4">
          本サービスでは、以下の公開データソースから価格情報を取得しています。
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">ソース名</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">取得データ</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">公開状況</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">robots.txt</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">アクセス頻度</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <SourceRow
                name="日本鉄鋼連盟（JISF）"
                data="鉄鋼製品価格（熱延・冷延・H形鋼・鉄筋・厚板）"
                access="一般公開"
                robots="制限なし"
                freq="月1回以内"
              />
              <SourceRow
                name="日本鉄リサイクル工業会（JISRI）"
                data="鉄スクラップ価格（H2・HS・H1・シュレッダー）"
                access="一般公開"
                robots="制限なし"
                freq="月1回以内"
              />
              <SourceRow
                name="東京製鐵株式会社"
                data="鉄スクラップ購入価格・鋼材販売価格"
                access="一般公開"
                robots="不存在（禁止なし）"
                freq="月1回以内"
              />
              <SourceRow
                name="World Bank Commodity Markets"
                data="国際非鉄金属価格（銅・アルミ・亜鉛・ニッケル等）"
                access="公開API"
                robots="—"
                freq="月1回以内"
              />
              <SourceRow
                name="U.S. EIA"
                data="原油・ナフサ価格"
                access="公開API"
                robots="—"
                freq="月1回以内"
              />
              <SourceRow
                name="経済産業省"
                data="石油化学製品価格（ナフサ・エチレン・プロピレン・ベンゼン）"
                access="一般公開CSV"
                robots="—"
                freq="月1回以内"
              />
            </tbody>
          </table>
        </div>
      </Section>

      {/* スクレイピングの法的根拠 */}
      <Section title="スクレイピングの法的根拠" titleEn="Legal Basis for Web Scraping">
        <p className="text-sm text-gray-600 mb-4">
          日本法（著作権法・不正競争防止法・不法行為法）の観点から、当サービスのデータ収集が適法である根拠を以下に説明します。
        </p>
        <ul className="space-y-3">
          <LegalPoint
            title="事実情報の収集"
            description="収集対象は「価格」という事実情報（facts）であり、著作権法上の著作物性が低いものです。著作権法は表現を保護するものであり、事実そのものは保護の対象外です（著作権法第2条第1項第1号）。"
          />
          <LegalPoint
            title="robots.txtの遵守"
            description="各データソースのrobots.txtを確認し、禁止されていないページのみアクセスしています。東京製鐵についてはrobots.txtが存在しないため、アクセス制限はありません。"
          />
          <LegalPoint
            title="アクセス頻度の制限"
            description="全てのスクレイピング対象に対し、アクセス頻度を月1回以内に制限しています。これにより、対象サイトのサーバーに過度な負荷をかけることなく、業務妨害に当たらないよう配慮しています。"
          />
          <LegalPoint
            title="User-Agentの明示"
            description="全てのHTTPリクエストにおいて、User-Agentヘッダーに「PriceTracker/1.0」およびプロジェクトURLを明記し、アクセス元を識別可能にしています。"
          />
        </ul>
      </Section>

      {/* 免責事項 */}
      <Section title="免責事項" titleEn="Disclaimer">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-3">
          <DisclaimerItem
            title="データの正確性・完全性"
            description="本サービスで提供するデータの正確性および完全性について、いかなる保証も行いません。データは各ソースから自動取得したものであり、取得・解析過程でのエラーが含まれる可能性があります。"
          />
          <DisclaimerItem
            title="投資判断・商業判断の免責"
            description="本サービスのデータを投資判断・商業判断の根拠として使用した場合に生じるいかなる損害についても、当サービスは一切の責任を負いません。最終的な意思決定は、必ずご自身の責任において行ってください。"
          />
          <DisclaimerItem
            title="データの更新停止"
            description="データソース側のウェブサイト構造の変更、サービスの停止、またはアクセス制限の追加等により、情報が更新されない場合があります。データの取得可否はソース側の状況に依存します。"
          />
        </div>
      </Section>

      {/* 著作権・出典表示 */}
      <Section title="著作権・出典表示" titleEn="Copyright &amp; Attribution">
        <p className="text-sm text-gray-600 mb-4">
          本サービスで表示するデータは、以下の各データソースから取得しています。
          各データソースの著作権は、それぞれの権利者に帰属します。
        </p>
        <div className="space-y-2">
          <AttributionItem
            source="日本鉄鋼連盟（JISF）"
            url="https://www.jisf.or.jp/"
            notice="鉄鋼統計データは一般社団法人日本鉄鋼連盟の公開情報に基づきます。"
          />
          <AttributionItem
            source="日本鉄リサイクル工業会（JISRI）"
            url="https://www.jisri.or.jp/"
            notice="鉄スクラップ価格データは一般社団法人日本鉄リサイクル工業会の公開情報に基づきます。"
          />
          <AttributionItem
            source="東京製鐵株式会社"
            url="https://www.tokyosteel.co.jp/"
            notice="鉄スクラップ購入価格・鋼材販売価格は東京製鐵株式会社の公表情報に基づきます。"
          />
          <AttributionItem
            source="World Bank Group"
            url="https://www.worldbank.org/"
            notice="Commodity price data from World Bank Commodity Markets (Pink Sheet). Licensed under CC BY 4.0."
          />
          <AttributionItem
            source="U.S. Energy Information Administration (EIA)"
            url="https://www.eia.gov/"
            notice="Energy price data from U.S. EIA Open Data API. Public domain (U.S. Government work)."
          />
          <AttributionItem
            source="経済産業省"
            url="https://www.meti.go.jp/"
            notice="石油化学製品価格データは経済産業省の公表統計に基づきます。政府統計の利用規約に従います。"
          />
        </div>
      </Section>

      {/* データ更新頻度 */}
      <Section title="データ更新頻度" titleEn="Data Update Frequency">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">ソース</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">取得方法</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">ソース更新頻度</th>
                <th className="px-4 py-2.5 text-left font-semibold text-gray-700">当サービスの取得頻度</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <FreqRow source="日本鉄鋼連盟（JISF）" method="HTMLスクレイピング" sourceFreq="月次" ourFreq="月1回（手動）" />
              <FreqRow source="日本鉄リサイクル工業会（JISRI）" method="HTMLスクレイピング" sourceFreq="月次" ourFreq="月1回（手動）" />
              <FreqRow source="東京製鐵株式会社" method="HTMLスクレイピング" sourceFreq="不定期（価格改定時）" ourFreq="月1回（手動）" />
              <FreqRow source="World Bank" method="公開API" sourceFreq="月次" ourFreq="週1回（自動）" />
              <FreqRow source="U.S. EIA" method="公開API" sourceFreq="週次" ourFreq="週1回（自動）" />
              <FreqRow source="経済産業省" method="CSV取得" sourceFreq="月次" ourFreq="週1回（自動）" />
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          ※ 自動取得はスケジューラにより定期実行されます。手動取得はダッシュボードの「データを更新」ボタンから実行できます。
        </p>
      </Section>
    </div>
  )
}

/* --- サブコンポーネント --- */

function Section({ title, titleEn, children }: { title: string; titleEn: string; children: React.ReactNode }) {
  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-bold text-gray-800 mb-1">{title}</h2>
      <p className="text-xs text-gray-400 mb-4">{titleEn}</p>
      {children}
    </section>
  )
}

function SourceRow({ name, data, access, robots, freq }: { name: string; data: string; access: string; robots: string; freq: string }) {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-2.5 font-medium text-gray-800">{name}</td>
      <td className="px-4 py-2.5 text-gray-600">{data}</td>
      <td className="px-4 py-2.5"><span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{access}</span></td>
      <td className="px-4 py-2.5 text-gray-600">{robots}</td>
      <td className="px-4 py-2.5 text-gray-600">{freq}</td>
    </tr>
  )
}

function LegalPoint({ title, description }: { title: string; description: string }) {
  return (
    <li className="flex gap-3">
      <span className="flex-shrink-0 mt-0.5 w-5 h-5 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center">
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      </span>
      <div>
        <p className="text-sm font-semibold text-gray-800">{title}</p>
        <p className="text-sm text-gray-600 mt-0.5">{description}</p>
      </div>
    </li>
  )
}

function DisclaimerItem({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <p className="text-sm font-semibold text-amber-800">{title}</p>
      <p className="text-sm text-amber-700 mt-0.5">{description}</p>
    </div>
  )
}

function AttributionItem({ source, url, notice }: { source: string; url: string; notice: string }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50">
      <div className="flex-shrink-0 mt-0.5 w-2 h-2 bg-brand-400 rounded-full" />
      <div>
        <a href={url} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-brand-700 hover:text-brand-900 hover:underline">
          {source}
          <svg className="inline-block w-3 h-3 ml-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
        <p className="text-xs text-gray-500 mt-0.5">{notice}</p>
      </div>
    </div>
  )
}

function FreqRow({ source, method, sourceFreq, ourFreq }: { source: string; method: string; sourceFreq: string; ourFreq: string }) {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-2.5 font-medium text-gray-800">{source}</td>
      <td className="px-4 py-2.5 text-gray-600">{method}</td>
      <td className="px-4 py-2.5 text-gray-600">{sourceFreq}</td>
      <td className="px-4 py-2.5 text-gray-600">{ourFreq}</td>
    </tr>
  )
}
