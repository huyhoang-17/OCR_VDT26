$ErrorActionPreference = 'Stop'

$ROOT = 'D:\OCR_VDT26'
$ASSETS = Join-Path $ROOT 'viettel-pptx\assets'
$LOCAL = Join-Path $ROOT 'slides\assets'
$OUT = Join-Path $ROOT 'slides\OCR_IDP_Viettel_2026.pptx'
$PDF = Join-Path $ROOT 'slides\OCR_IDP_Viettel_2026.pdf'
$RENDER = Join-Path $ROOT 'slides\rendered'

$RED = 0x2E1AEE       # Office stores BGR: #EE1A2E
$RED_ACCENT = 0x3300EE
$GRAY_DARK = 0x5A5A5A
$GRAY_MID = 0x808080
$GRAY_LIGHT = 0xB4B4B4
$GRAY_PALE = 0xE6E6E6
$WHITE = 0xFFFFFF
$BLACK = 0x000000
$FONT_HEAD = 'PF BeauSans Pro'
$FONT_BODY = 'Sarabun'

function Add-Text {
    param($Slide, [string]$Text, [double]$X, [double]$Y, [double]$W, [double]$H,
          [double]$Size = 18, [int]$Color = 0, [string]$Font = 'Sarabun',
          [bool]$Bold = $false, [int]$Align = 1, [int]$VAlign = 3)
    $s = $Slide.Shapes.AddTextbox(1, $X, $Y, $W, $H)
    $s.Fill.Visible = 0
    $s.Line.Visible = 0
    $s.TextFrame2.MarginLeft = 4
    $s.TextFrame2.MarginRight = 4
    $s.TextFrame2.MarginTop = 2
    $s.TextFrame2.MarginBottom = 2
    $s.TextFrame2.WordWrap = -1
    $s.TextFrame2.AutoSize = 0
    $s.TextFrame2.VerticalAnchor = $VAlign
    $s.TextFrame2.TextRange.Text = $Text
    $s.TextFrame2.TextRange.Font.Name = $Font
    $s.TextFrame2.TextRange.Font.Size = $Size
    $s.TextFrame2.TextRange.Font.Bold = $(if ($Bold) { -1 } else { 0 })
    $s.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = $Color
    $s.TextFrame2.TextRange.ParagraphFormat.Alignment = $Align
}

function Add-Box {
    param($Slide, [string]$Text, [double]$X, [double]$Y, [double]$W, [double]$H,
          [int]$Fill, [int]$TextColor = 0xFFFFFF, [double]$Size = 18,
          [bool]$Bold = $true, [int]$ShapeType = 5, [int]$LineColor = -1)
    $s = $Slide.Shapes.AddShape($ShapeType, $X, $Y, $W, $H)
    $s.Fill.Visible = -1
    $s.Fill.Solid()
    $s.Fill.ForeColor.RGB = $Fill
    if ($LineColor -ge 0) {
        $s.Line.Visible = -1
        $s.Line.ForeColor.RGB = $LineColor
        $s.Line.Weight = 1.2
    } else { $s.Line.Visible = 0 }
    $s.TextFrame2.MarginLeft = 8
    $s.TextFrame2.MarginRight = 8
    $s.TextFrame2.MarginTop = 4
    $s.TextFrame2.MarginBottom = 4
    $s.TextFrame2.WordWrap = -1
    $s.TextFrame2.VerticalAnchor = 3
    $s.TextFrame2.TextRange.Text = $Text
    $s.TextFrame2.TextRange.Font.Name = $(if ($Bold) { $FONT_HEAD } else { $FONT_BODY })
    $s.TextFrame2.TextRange.Font.Size = $Size
    $s.TextFrame2.TextRange.Font.Bold = $(if ($Bold) { -1 } else { 0 })
    $s.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = $TextColor
    $s.TextFrame2.TextRange.ParagraphFormat.Alignment = 2
}

function Add-Line {
    param($Slide, [double]$X1, [double]$Y1, [double]$X2, [double]$Y2,
          [int]$Color = 0xB4B4B4, [double]$Weight = 1.5, [bool]$Arrow = $false)
    $s = $Slide.Shapes.AddLine($X1, $Y1, $X2, $Y2)
    $s.Line.ForeColor.RGB = $Color
    $s.Line.Weight = $Weight
    if ($Arrow) { $s.Line.EndArrowheadStyle = 3 }
}

function Add-Image {
    param($Slide, [string]$Path, [double]$X, [double]$Y, [double]$W, [double]$H)
    [void]$Slide.Shapes.AddPicture($Path, 0, -1, $X, $Y, $W, $H)
}

function Add-Background {
    param($Slide, [string]$Variant = 'corner-tr')
    if ($Variant -eq 'none') { return }
    if ($Variant -eq 'corner-tr' -or $Variant -eq 'dual-corners') {
        $s = $Slide.Shapes.AddShape(9, 1224, -180, 432, 432)
        $s.Fill.Solid(); $s.Fill.ForeColor.RGB = $GRAY_PALE; $s.Line.Visible = 0
    }
    if ($Variant -eq 'corner-bl' -or $Variant -eq 'dual-corners') {
        $s = $Slide.Shapes.AddShape(9, -180, 510, 396, 396)
        $s.Fill.Solid(); $s.Fill.ForeColor.RGB = $GRAY_PALE; $s.Line.Visible = 0
    }
    if ($Variant -eq 'side-arc-left') {
        $s = $Slide.Shapes.AddShape(9, -576, 72, 648, 648)
        $s.Fill.Solid(); $s.Fill.ForeColor.RGB = $GRAY_PALE; $s.Line.Visible = 0
    }
    if ($Variant -eq 'red-watermark') {
        $s = $Slide.Shapes.AddShape(9, 1008, -216, 648, 648)
        $s.Fill.Solid(); $s.Fill.ForeColor.RGB = $RED; $s.Fill.Transparency = 0.92
        $s.Line.Visible = 0
    }
}

function Add-Footer {
    param($Slide)
    Add-Image $Slide (Join-Path $ASSETS 'footer_bar.png') 0 738.648 1440 71.352
    Add-Image $Slide (Join-Path $ASSETS 'logo_white.png') 1239.84 751.32 132.984 53.64
    Add-Text $Slide 'www.viettel.com.vn' 39.528 754.344 625.032 32.688 21 $GRAY_LIGHT $FONT_BODY $false 1 3
}

function Add-Title {
    param($Slide, [string]$Title, [string]$Subtitle = '', [string]$Bg = 'corner-tr')
    Add-Background $Slide $Bg
    Add-Text $Slide $Title.ToUpperInvariant() 36 34 1368 64 45 $RED $FONT_HEAD $true 2 3
    if ($Subtitle) { Add-Text $Slide $Subtitle 72 92 1296 42 18 $BLACK $FONT_BODY $false 2 3 }
}

function Add-Kpi {
    param($Slide, [string]$Label, [string]$Value, [double]$X, [double]$Y,
          [double]$W = 230, [int]$Fill = 0xF3F3F4, [int]$ValueColor = 0x2E1AEE)
    $s = $Slide.Shapes.AddShape(5, $X, $Y, $W, 112)
    $s.Fill.Solid(); $s.Fill.ForeColor.RGB = $Fill; $s.Line.Visible = 0
    Add-Text $Slide $Value $X ($Y + 11) $W 56 31 $ValueColor $FONT_HEAD $true 2 3
    Add-Text $Slide $Label $X ($Y + 66) $W 32 15 $GRAY_DARK $FONT_BODY $false 2 3
}

function Add-Bullets {
    param($Slide, [string[]]$Items, [double]$X, [double]$Y, [double]$W, [double]$H,
          [double]$Size = 18, [int]$Color = 0)
    $text = ($Items | ForEach-Object { "•  $_" }) -join "`r`n"
    Add-Text $Slide $text $X $Y $W $H $Size $Color $FONT_BODY $false 1 1
}

function Add-Table {
    param($Slide, [object[][]]$Data, [double]$X, [double]$Y, [double]$W, [double]$H,
          [double[]]$Widths = $null, [double]$FontSize = 14)
    $rows = $Data.Count; $cols = $Data[0].Count
    $shape = $Slide.Shapes.AddTable($rows, $cols, $X, $Y, $W, $H)
    $table = $shape.Table
    if ($Widths) { for ($c = 1; $c -le $cols; $c++) { $table.Columns.Item($c).Width = $Widths[$c-1] } }
    for ($r = 1; $r -le $rows; $r++) {
        for ($c = 1; $c -le $cols; $c++) {
            $cell = $table.Cell($r, $c).Shape
            $cell.TextFrame2.TextRange.Text = [string]$Data[$r-1][$c-1]
            $cell.TextFrame2.TextRange.Font.Name = $FONT_BODY
            $cell.TextFrame2.TextRange.Font.Size = $FontSize
            $cell.TextFrame2.TextRange.Font.Bold = $(if ($r -eq 1) { -1 } else { 0 })
            $cell.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = $(if ($r -eq 1) { $WHITE } else { $BLACK })
            $cell.TextFrame2.TextRange.ParagraphFormat.Alignment = $(if ($c -eq 1) { 1 } else { 2 })
            $cell.TextFrame2.VerticalAnchor = 3
            $cell.Fill.Solid(); $cell.Fill.ForeColor.RGB = $(if ($r -eq 1) { $RED } elseif ($r % 2 -eq 0) { 0xF3F3F4 } else { $WHITE })
            $cell.Line.ForeColor.RGB = $GRAY_LIGHT; $cell.Line.Weight = 0.6
        }
    }
}

function Add-SectionSlide {
    param($Presentation, [string]$Photo, [string]$Title, [string]$Description)
    $slide = $Presentation.Slides.Add($Presentation.Slides.Count + 1, 12)
    Add-Image $slide $Photo 0 0 662 725
    $overlay = $slide.Shapes.AddShape(1, 0, 0, 662, 725)
    $overlay.Fill.Solid(); $overlay.Fill.ForeColor.RGB = $BLACK; $overlay.Fill.Transparency = 0.62; $overlay.Line.Visible = 0
    Add-Image $slide (Join-Path $ASSETS 'section_blob.png') 536 187 545 350
    Add-Text $slide $Title.ToUpperInvariant() 638 248 336 164 38 $WHITE $FONT_HEAD $true 2 3
    Add-Text $slide $Description 1010 260 350 135 18 $GRAY_DARK $FONT_BODY $false 1 3
    Add-Footer $slide
    return $slide
}

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = -1
$pres = $ppt.Presentations.Add()
$pres.PageSetup.SlideWidth = 1440
$pres.PageSetup.SlideHeight = 810

try {
    # 01 — Cover
    $s = $pres.Slides.Add(1, 12)
    Add-Image $s (Join-Path $LOCAL 'form1.png') 0 -570 1440 2038
    $shade = $s.Shapes.AddShape(1, 0, 0, 1440, 810)
    $shade.Fill.Solid(); $shade.Fill.ForeColor.RGB = $BLACK; $shade.Fill.Transparency = 0.38; $shade.Line.Visible = 0
    Add-Image $s (Join-Path $ASSETS 'cover_subtitle_pill.png') 0 310 448 74
    Add-Text $s 'BÁO CÁO DỰ ÁN · 2026' 14 324 420 42 20 $RED_ACCENT $FONT_BODY $true 1 3
    Add-Image $s (Join-Path $ASSETS 'cover_title_pill.png') 87 405 530 123
    Add-Text $s 'HỆ THỐNG OCR-IDP' 117 430 470 64 38 $WHITE $FONT_HEAD $false 2 3
    Add-Text $s 'Số hóa biểu mẫu chứng khoán tiếng Việt`r`nTừ tài liệu đến dữ liệu nghiệp vụ chủ động' 760 330 570 150 27 $WHITE $FONT_HEAD $true 1 3
    Add-Footer $s

    # 02 — Agenda
    $s = $pres.Slides.Add(2, 12); Add-Title $s 'NỘI DUNG TRÌNH BÀY' 'Hành trình từ bài toán OCR đến kiểm tra tuân thủ' 'side-arc-left'
    $agenda = @(
        @('01','Bài toán & dữ liệu'), @('02','Kiến trúc OCR-IDP'), @('03','Đánh giá OCR & extractor'),
        @('04','Tầng nghiệp vụ & LLM'), @('05','Demo, kết luận & roadmap')
    )
    for ($i=0; $i -lt $agenda.Count; $i++) {
        $y = 160 + $i*103; $fill = @($RED,$GRAY_DARK,$GRAY_MID,$GRAY_DARK,$RED)[$i]
        Add-Box $s $agenda[$i][0] 180 $y 68 68 $fill $WHITE 24 $true 9
        Add-Box $s $agenda[$i][1] 275 ($y+4) 830 60 $(if ($i -eq 0 -or $i -eq 4) { $RED } else { $GRAY_MID }) $WHITE 22 $true 5
    }
    Add-Footer $s

    # 03 — Problem & objectives
    $s = $pres.Slides.Add(3, 12); Add-Title $s 'BÀI TOÁN & MỤC TIÊU' 'Giảm nhập liệu thủ công, tăng khả năng kiểm chứng và khai thác dữ liệu' 'dual-corners'
    Add-Text $s 'THÁCH THỨC' 95 158 490 46 25 $RED $FONT_HEAD $true 2 3
    Add-Bullets $s @('PDF số và ảnh scan nhiều trang','Tiếng Việt có dấu, chất lượng ảnh không đồng đều','Bảng, checkbox/radio, trường nhiều dòng','Schema khác nhau theo từng eform') 90 215 520 310 20 $BLACK
    Add-Line $s 690 180 690 610 $GRAY_LIGHT 2 $false
    Add-Text $s 'MỤC TIÊU' 800 158 490 46 25 $RED $FONT_HEAD $true 2 3
    Add-Bullets $s @('PDF/ảnh → JSON đúng schema','So sánh nhiều OCR engine định lượng','Phát hiện dữ liệu thiếu/sai/độ tin cậy thấp','Kiểm tra nghiệp vụ và sinh biên bản tuân thủ') 790 215 540 310 20 $BLACK
    Add-Box $s 'TỪ NHẬP LIỆU THỤ ĐỘNG → PHÁT HIỆN SAI SÓT CHỦ ĐỘNG' 270 590 900 70 $RED $WHITE 24 $true 5
    Add-Footer $s

    # 04 — Dataset
    $s = $pres.Slides.Add(4, 12); Add-Title $s 'DỮ LIỆU THỰC NGHIỆM' '9 loại eform chứng khoán · tài liệu nhiều trang · ground-truth JSON' 'corner-tr'
    Add-Kpi $s 'Biểu mẫu eform' '9' 90 160 230 $RED $WHITE
    Add-Kpi $s 'Tổng số trang' '27' 350 160 230 $GRAY_DARK $WHITE
    Add-Kpi $s 'Trường ground-truth' '472' 610 160 250 $GRAY_MID $WHITE
    Add-Kpi $s 'PDF số / bản scan' '1 / 8' 890 160 270 $RED $WHITE
    Add-Image $s (Join-Path $LOCAL 'form93.png') 1000 305 260 370
    Add-Text $s 'CẤU TRÚC DỮ LIỆU' 95 330 500 42 24 $RED $FONT_HEAD $true 1 3
    Add-Box $s 'data/raw/form_<N>.pdf' 100 385 540 60 $GRAY_DARK $WHITE 20 $false 5
    Add-Box $s 'data/ground_truth/expect_<N>.json' 100 475 540 60 $GRAY_MID $WHITE 20 $false 5
    Add-Line $s 370 445 370 475 $RED 2 $true
    Add-Text $s 'Mỗi loại hiện có 1 tài liệu → pilot benchmark, chưa phải test set độc lập.' 100 575 760 55 18 $GRAY_DARK $FONT_BODY $false 1 3
    Add-Footer $s

    # 05 — Architecture
    $s = $pres.Slides.Add(5, 12); Add-Title $s 'KIẾN TRÚC END-TO-END' 'Các component độc lập, thay thế được; JSON là ranh giới giữa OCR và nghiệp vụ' 'none'
    $labels = @('PDF / ẢNH','TIỀN XỬ LÝ','OCR','LAYOUT','EXTRACTOR','JSON','BUSINESS RULES')
    $colors = @($GRAY_DARK,$GRAY_MID,$RED,$GRAY_DARK,$GRAY_MID,$RED,$GRAY_DARK)
    for ($i=0; $i -lt $labels.Count; $i++) {
        $x=42+$i*195
        Add-Box $s $labels[$i] $x 280 165 95 $colors[$i] $WHITE 17 $true 5
        if ($i -lt $labels.Count-1) { Add-Line $s ($x+165) 328 ($x+190) 328 $RED 2.5 $true }
    }
    Add-Text $s 'Deskew · denoise · crop' 220 410 190 42 15 $GRAY_DARK $FONT_BODY $false 2 3
    Add-Text $s '5 OCR engines' 420 410 165 42 15 $GRAY_DARK $FONT_BODY $false 2 3
    Add-Text $s 'Regex · fuzzy · layout' 800 410 205 42 15 $GRAY_DARK $FONT_BODY $false 2 3
    Add-Text $s '41 luật / 9 eform' 1205 410 180 42 15 $GRAY_DARK $FONT_BODY $false 2 3
    Add-Box $s 'CLI' 420 540 150 58 $RED $WHITE 20 $true 5
    Add-Box $s 'REST API' 645 540 180 58 $GRAY_DARK $WHITE 20 $true 5
    Add-Box $s 'STREAMLIT WEB' 900 540 230 58 $GRAY_MID $WHITE 20 $true 5
    Add-Footer $s

    # 06 — Section OCR
    [void](Add-SectionSlide $pres (Join-Path $LOCAL 'form93.png') 'OCR & TRÍCH XUẤT' 'Từ trang tài liệu không đồng nhất đến JSON theo schema.')

    # 07 — Preprocess
    $s = $pres.Slides.Add(7, 12); Add-Title $s 'TIỀN XỬ LÝ TÀI LIỆU' 'Chuẩn hóa đầu vào trước OCR, giữ nguyên ranh giới trang' 'corner-tr'
    $steps = @('RENDER PDF','DESKEW','DENOISE','CONTRAST','AUTO CROP')
    $desc = @('PyMuPDF · 300 DPI','Xoay thẳng trang','Khử nhiễu nền','CLAHE / binarize','Cắt vùng nội dung')
    for ($i=0; $i -lt 5; $i++) {
        $x=95+$i*250; $fill=@($RED,$GRAY_DARK,$GRAY_MID,$GRAY_DARK,$RED)[$i]
        Add-Box $s ([string]($i+1)) $x 220 72 72 $fill $WHITE 28 $true 9
        Add-Box $s $steps[$i] ($x-30) 320 180 62 $fill $WHITE 16 $true 5
        Add-Text $s $desc[$i] ($x-45) 400 210 60 16 $GRAY_DARK $FONT_BODY $false 2 3
        if ($i -lt 4) { Add-Line $s ($x+74) 256 ($x+215) 256 $GRAY_LIGHT 2 $true }
    }
    Add-Box $s 'FAST PATH: PDF có text-layer đủ sạch → bỏ qua OCR' 305 555 830 65 $GRAY_PALE $RED 22 $true 5 $GRAY_LIGHT
    Add-Footer $s

    # 08 — OCR engines
    $s = $pres.Slides.Add(8, 12); Add-Title $s 'OCR ĐA ENGINE' 'Một interface chung, lựa chọn theo môi trường và đặc tính tài liệu' 'none'
    $data = @(
        @('Engine','Điểm mạnh','Hạn chế','Vai trò'),
        @('RapidOCR','Nhẹ, CPU, ổn định','Yếu dấu tiếng Việt','Mặc định'),
        @('Tesseract','Nhanh, dễ triển khai','Nhạy tiền xử lý','Đối chứng'),
        @('VietOCR','Giữ dấu tiếng Việt','Chậm, cần Torch','Chất lượng'),
        @('EasyOCR / Paddle','Đa ngôn ngữ','Dependency nặng','Mở rộng')
    )
    Add-Table $s $data 75 170 1290 355 @(230,360,350,350) 16
    Add-Box $s 'RapidOCR detection' 220 575 300 62 $RED $WHITE 19 $true 5
    Add-Line $s 520 606 650 606 $RED 2.5 $true
    Add-Box $s 'VietOCR recognition' 650 575 320 62 $GRAY_DARK $WHITE 19 $true 5
    Add-Line $s 970 606 1080 606 $RED 2.5 $true
    Add-Box $s 'Text có dấu' 1080 575 200 62 $GRAY_MID $WHITE 19 $true 5
    Add-Footer $s

    # 09 — Hybrid extraction
    $s = $pres.Slides.Add(9, 12); Add-Title $s 'TRÍCH XUẤT HYBRID' 'Kết hợp nhiều tín hiệu thay vì phụ thuộc một kỹ thuật duy nhất' 'none'
    $c1=$s.Shapes.AddShape(9,270,210,360,360); $c1.Fill.Solid();$c1.Fill.ForeColor.RGB=$RED;$c1.Fill.Transparency=0.18;$c1.Line.Visible=0
    $c2=$s.Shapes.AddShape(9,530,210,360,360); $c2.Fill.Solid();$c2.Fill.ForeColor.RGB=$GRAY_DARK;$c2.Fill.Transparency=0.22;$c2.Line.Visible=0
    $c3=$s.Shapes.AddShape(9,400,390,360,300); $c3.Fill.Solid();$c3.Fill.ForeColor.RGB=$GRAY_MID;$c3.Fill.Transparency=0.20;$c3.Line.Visible=0
    Add-Text $s 'REGEX / RULE' 280 310 270 52 24 $WHITE $FONT_HEAD $true 2 3
    Add-Text $s 'FUZZY / ANCHOR' 610 310 240 52 24 $WHITE $FONT_HEAD $true 2 3
    Add-Text $s 'LAYOUT / HÌNH HỌC' 455 535 255 52 22 $WHITE $FONT_HEAD $true 2 3
    Add-Box $s 'LLM tùy chọn`r`nrepair trường yếu' 980 265 280 110 $RED $WHITE 20 $true 5
    Add-Box $s 'Chuẩn hóa`r`nngày · tiền · lựa chọn' 980 435 280 110 $GRAY_DARK $WHITE 20 $true 5
    Add-Text $s 'Extractor dò nhãn ở dạng không dấu nhưng giữ nguyên giá trị tiếng Việt có dấu.' 870 610 480 55 17 $GRAY_DARK $FONT_BODY $false 2 3
    Add-Footer $s

    # 10 — JSON & validation
    $s = $pres.Slides.Add(10, 12); Add-Title $s 'JSON, CHUẨN HÓA & VALIDATION' 'Đầu ra có cấu trúc, truy vết confidence và cảnh báo từng trường' 'corner-bl'
    $json = '{`r`n  "form_id": "eform1",`r`n  "results": {`r`n    "Menhgia...": "10000",`r`n    "Ngayketthuc...": "2025-11-30"`r`n  },`r`n  "_meta": {`r`n    "confidence": {...},`r`n    "warnings": [...]`r`n  }`r`n}'
    Add-Box $s $json 90 170 550 470 $GRAY_DARK $WHITE 17 $false 5
    $vals=@(
        @('01','NORMALIZE','Ngày, tiền, mã định danh, lựa chọn'),
        @('02','VALIDATE','Thiếu · sai định dạng · confidence thấp'),
        @('03','TRACE','Nguồn extractor, trạng thái và cảnh báo')
    )
    for($i=0;$i -lt 3;$i++){
        $y=185+$i*150; $fill=@($RED,$GRAY_MID,$GRAY_DARK)[$i]
        Add-Box $s $vals[$i][0] 760 $y 64 64 $fill $WHITE 23 $true 9
        Add-Text $s $vals[$i][1] 850 $y 400 38 22 $RED $FONT_HEAD $true 1 3
        Add-Text $s $vals[$i][2] 850 ($y+42) 460 55 18 $GRAY_DARK $FONT_BODY $false 1 3
    }
    Add-Footer $s

    # 11 — Evaluation methodology
    $s = $pres.Slides.Add(11, 12); Add-Title $s 'PHƯƠNG PHÁP ĐÁNH GIÁ OCR' 'So sánh JSON dự đoán với ground-truth theo từng trường' 'none'
    Add-Box $s 'form_<N>.pdf' 90 240 270 78 $GRAY_DARK $WHITE 21 $true 5
    Add-Box $s 'expect_<N>.json' 90 420 270 78 $GRAY_MID $WHITE 21 $true 5
    Add-Line $s 360 280 570 360 $RED 2.5 $true; Add-Line $s 360 460 570 380 $RED 2.5 $true
    Add-Box $s 'COMPARE DOCUMENTS' 570 315 320 100 $RED $WHITE 22 $true 5
    $metrics=@('Accuracy/trường','Exact-match/form','Precision · Recall · F1','Missing · OCR · Format','Thời gian xử lý')
    for($i=0;$i -lt $metrics.Count;$i++){
        Add-Box $s $metrics[$i] 1010 (165+$i*93) 290 58 $(if($i -eq 0){$RED}elseif($i%2){$GRAY_DARK}else{$GRAY_MID}) $WHITE 17 $true 5
    }
    Add-Text $s 'Lưu ý: 9 tài liệu / 9 eform → kết quả mang tính pilot benchmark.' 420 590 540 58 18 $RED $FONT_BODY $true 2 3
    Add-Footer $s

    # 12 — Overall OCR results
    $s = $pres.Slides.Add(12, 12); Add-Title $s 'KẾT QUẢ 3 OCR ENGINE' 'Cùng 9 extractor · ép OCR toàn bộ 27 trang · 472 trường' 'corner-tr'
    $eng=@(@('VietOCR',47.5,$RED),@('RapidOCR',47.2,$GRAY_DARK),@('Tesseract',47.0,$GRAY_MID))
    for($i=0;$i -lt 3;$i++){
        $y=205+$i*130; Add-Text $s $eng[$i][0] 110 $y 200 45 22 $BLACK $FONT_HEAD $true 1 3
        $bg=$s.Shapes.AddShape(5,330,$y,700,48);$bg.Fill.Solid();$bg.Fill.ForeColor.RGB=0xF3F3F4;$bg.Line.Visible=0
        $bar=$s.Shapes.AddShape(5,330,$y,[double]$eng[$i][1]*13.5,48);$bar.Fill.Solid();$bar.Fill.ForeColor.RGB=$eng[$i][2];$bar.Line.Visible=0
        Add-Text $s ("{0:N1}%" -f $eng[$i][1]) 1050 $y 130 45 24 $eng[$i][2] $FONT_HEAD $true 2 3
    }
    Add-Kpi $s 'Precision tốt nhất · RapidOCR' '97,5%' 210 590 290 $RED $WHITE
    Add-Kpi $s 'Chênh lệch accuracy tối đa' '0,5 điểm %' 550 590 300 $GRAY_DARK $WHITE
    Add-Kpi $s 'Exact-match toàn form' '0%' 900 590 290 $GRAY_MID $WHITE
    Add-Footer $s

    # 13 — Per-form results
    $s = $pres.Slides.Add(13, 12); Add-Title $s 'KẾT QUẢ THEO EFORM' 'Accuracy theo trường khi chạy --kind scan' 'none'
    $data=@(
      @('eform','RapidOCR','Tesseract','VietOCR','Tốt nhất'),
      @('eform1','19,1%','48,9%','61,7%','VietOCR'),@('eform100','64,0%','60,0%','58,0%','RapidOCR'),
      @('eform5','58,6%','55,2%','50,0%','RapidOCR'),@('eform69','59,4%','57,8%','56,2%','RapidOCR'),
      @('eform7','38,9%','27,8%','31,9%','RapidOCR'),@('eform85','57,1%','71,4%','61,9%','Tesseract'),
      @('eform92','62,1%','48,3%','44,8%','RapidOCR'),@('eform93','18,2%','16,4%','16,4%','RapidOCR'),
      @('eform94','55,3%','55,3%','56,6%','VietOCR')
    )
    Add-Table $s $data 115 155 1210 510 @(210,230,230,230,310) 14
    Add-Text $s 'RapidOCR tốt nhất trên 6/9 extractor · VietOCR nổi bật ở eform1 · Tesseract nổi bật ở eform85.' 150 680 1140 35 17 $RED $FONT_BODY $true 2 3
    Add-Footer $s

    # 14 — Error analysis
    $s = $pres.Slides.Add(14, 12); Add-Title $s 'PHÂN TÍCH LỖI & GIỚI HẠN' 'Luồng PDF: 257/472 trường đúng · 207 trường missing' 'dual-corners'
    Add-Kpi $s 'Accuracy/trường · PDF' '54,4%' 95 160 270 $RED $WHITE
    Add-Kpi $s 'Accuracy/trường · scan' '47,2%' 390 160 270 $GRAY_DARK $WHITE
    Add-Kpi $s 'Exact-match/form' '0%' 685 160 270 $GRAY_MID $WHITE
    Add-Kpi $s 'Precision · PDF' '98,0%' 980 160 270 $RED $WHITE
    Add-Text $s 'NGUYÊN NHÂN CHÍNH' 105 340 520 45 24 $RED $FONT_HEAD $true 1 3
    Add-Bullets $s @('Regex chưa phủ toàn bộ trường','Bảng BagPart eform69/eform93 chưa đầy đủ','OCR mất dấu hoặc bỏ sót vùng','Mỗi eform chỉ có một tài liệu để tinh chỉnh') 105 400 580 235 19 $BLACK
    Add-Text $s 'HƯỚNG CẢI THIỆN' 790 340 520 45 24 $RED $FONT_HEAD $true 1 3
    Add-Bullets $s @('Table extraction theo hàng/cột','Bổ sung dữ liệu held-out','Schema-driven extractor','Human review cho trường confidence thấp') 790 400 530 235 19 $BLACK
    Add-Footer $s

    # 15 — Section business
    [void](Add-SectionSlide $pres (Join-Path $LOCAL 'form94.png') 'TẦNG NGHIỆP VỤ' 'Biến JSON đã số hóa thành công cụ phát hiện sai sót chủ động.')

    # 16 — Business rules
    $s = $pres.Slides.Add(16, 12); Add-Title $s 'BUSINESS-RULE ENGINE' 'Luật YAML theo eform · tính toán tất định · không dùng eval' 'none'
    $rules=@(
      @('SỐ HỌC','Tổng vốn ≈ số lượng × mệnh giá',$RED),
      @('ĐỐI SOÁT','Trong nước + nước ngoài = tổng',$GRAY_DARK),
      @('THỜI GIAN','Ngày báo cáo ≥ ngày kết thúc',$GRAY_MID)
    )
    for($i=0;$i -lt 3;$i++){
        $x=80+$i*450; Add-Box $s $rules[$i][0] $x 180 360 68 $rules[$i][2] $WHITE 21 $true 5
        Add-Text $s $rules[$i][1] $x 275 360 95 19 $BLACK $FONT_BODY $false 2 3
    }
    $yaml='id: eform1.capital_product`r`nseverity: error`r`noperation: equals_product`r`nactual: total_raised`r`nfactors: [issued_shares, par_value]'
    Add-Box $s $yaml 150 430 520 210 $GRAY_DARK $WHITE 18 $false 5
    Add-Bullets $s @('PASS: đủ dữ liệu và điều kiện đúng','VIOLATION: đủ dữ liệu nhưng điều kiện sai','SKIPPED: thiếu/sai kiểu dữ liệu, không được xem là đạt','Severity error/warning chỉ hậu quả khi luật bị vi phạm') 760 430 560 210 18 $BLACK
    Add-Footer $s

    # 17 — Compliance & LLM
    $s = $pres.Slides.Add(17, 12); Add-Title $s 'BIÊN BẢN TUÂN THỦ & LLM' 'LLM chỉ diễn đạt; mọi phép tính và kết luận do mã lệnh thực hiện' 'corner-tr'
    $flow=@('JSON ĐÃ TRÍCH','RULE ENGINE','KẾT QUẢ ĐÃ TÍNH','GEMINI / OPENAI','DOCX / PDF')
    $cols=@($GRAY_DARK,$RED,$GRAY_MID,$GRAY_DARK,$RED)
    for($i=0;$i -lt 5;$i++){
        $x=55+$i*276; Add-Box $s $flow[$i] $x 240 220 80 $cols[$i] $WHITE 17 $true 5
        if($i -lt 4){Add-Line $s ($x+220) 280 ($x+266) 280 $RED 2.5 $true}
    }
    Add-Box $s 'Payload LLM chỉ gồm:`r`nstatus · counts · violations · actual/expected' 150 430 500 140 $GRAY_PALE $BLACK 20 $false 5 $GRAY_LIGHT
    Add-Box $s 'Guardrail:`r`nkhông tính lại · không thêm dữ kiện · fallback deterministic' 790 430 500 140 $GRAY_PALE $BLACK 20 $false 5 $GRAY_LIGHT
    Add-Text $s 'Provider: deterministic | Gemini 3 Flash | OpenAI' 400 620 640 45 18 $RED $FONT_BODY $true 2 3
    Add-Footer $s

    # 18 — Compliance evaluation + demo
    $s = $pres.Slides.Add(18, 12); Add-Title $s 'ĐÁNH GIÁ TẦNG NGHIỆP VỤ & DEMO' 'Benchmark tách biệt OCR · lỗi nhân tạo có nhãn rõ ràng' 'none'
    Add-Kpi $s 'Luật nghiệp vụ' '41' 90 155 230 $RED $WHITE
    Add-Kpi $s 'Eform có luật' '9' 350 155 230 $GRAY_DARK $WHITE
    Add-Kpi $s 'Ca chèn lỗi' '35' 610 155 230 $GRAY_MID $WHITE
    Add-Kpi $s 'Precision / Recall / F1' '100%' 870 155 330 $RED $WHITE
    Add-Text $s 'DEMO WEB' 95 330 300 42 24 $RED $FONT_HEAD $true 1 3
    Add-Box $s 'Kết luận`r`ncompliant' 100 390 240 100 $GRAY_PALE $BLACK 20 $false 5 $GRAY_LIGHT
    Add-Box $s 'Đạt`r`n2' 360 390 180 100 $GRAY_PALE $BLACK 20 $false 5 $GRAY_LIGHT
    Add-Box $s 'Vi phạm`r`n0' 560 390 180 100 $GRAY_PALE $BLACK 20 $false 5 $GRAY_LIGHT
    Add-Box $s 'Chưa đánh giá`r`n2' 760 390 220 100 $GRAY_PALE $BLACK 20 $false 5 $GRAY_LIGHT
    $ui=@(@('Mã luật','Mức độ khi vi phạm','Kết quả'),@('capital_product','error','skipped'),@('offering_after_certificate','error','pass'))
    Add-Table $s $ui 100 525 880 125 @(360,280,240) 13
    Add-Box $s 'CLI' 1080 365 210 60 $RED $WHITE 19 $true 5
    Add-Box $s 'REST API' 1080 455 210 60 $GRAY_DARK $WHITE 19 $true 5
    Add-Box $s 'STREAMLIT' 1080 545 210 60 $GRAY_MID $WHITE 19 $true 5
    Add-Footer $s

    # 19 — Conclusion & roadmap
    $s = $pres.Slides.Add(19, 12); Add-Title $s 'KẾT LUẬN & ROADMAP' 'Đủ hoàn thiện ở mức đồ án; còn khoảng cách tới production' 'red-watermark'
    Add-Text $s 'ĐÃ HOÀN THÀNH' 100 160 500 44 25 $RED $FONT_HEAD $true 1 3
    Add-Bullets $s @('Pipeline PDF/ảnh → JSON cho 9 eform','So sánh 3 OCR engine định lượng','41 luật nghiệp vụ + biên bản DOCX/PDF','CLI · API · Web · Docker · 103 test') 100 220 560 260 20 $BLACK
    Add-Text $s 'ƯU TIÊN TIẾP THEO' 800 160 500 44 25 $RED $FONT_HEAD $true 1 3
    Add-Bullets $s @('Table extraction eform69/eform93','Bổ sung dữ liệu train/dev/test độc lập','Đổi compliant → needs_review khi error bị skipped','Xác nhận catalogue luật với chuyên gia nghiệp vụ') 790 220 540 260 20 $BLACK
    Add-Box $s 'THÔNG ĐIỆP CHÍNH' 310 535 820 56 $RED $WHITE 22 $true 5
    Add-Text $s 'Hệ thống không chỉ số hóa tài liệu, mà còn biến dữ liệu thành tín hiệu kiểm soát chủ động.' 270 605 900 65 21 $GRAY_DARK $FONT_BODY $true 2 3
    Add-Footer $s

    # 20 — Closing
    $s = $pres.Slides.Add(20, 12)
    $circle=$s.Shapes.AddShape(9,-80,180,510,510);$circle.Fill.Solid();$circle.Fill.ForeColor.RGB=$GRAY_PALE;$circle.Line.Visible=0
    Add-Text $s 'XIN TRÂN TRỌNG`r`nCẢM ƠN' 40 310 520 155 48 $RED_ACCENT $FONT_HEAD $false 1 3
    foreach($d in @(@(120,$GRAY_MID),@(160,$RED),@(200,$GRAY_DARK))){$dot=$s.Shapes.AddShape(9,$d[0],500,18,18);$dot.Fill.Solid();$dot.Fill.ForeColor.RGB=$d[1];$dot.Line.Visible=0}
    Add-Image $s (Join-Path $ASSETS 'logo.png') 810 255 470 160
    Add-Text $s 'OCR-IDP · VIETNAMESE SECURITIES FORMS' 760 450 600 55 22 $GRAY_DARK $FONT_HEAD $true 2 3
    Add-Text $s 'Q&A' 920 540 280 90 42 $RED $FONT_HEAD $true 2 3
    Add-Footer $s

    New-Item -ItemType Directory -Force -Path (Split-Path $OUT) | Out-Null
    if (Test-Path -LiteralPath $OUT) { Remove-Item -LiteralPath $OUT -Force }
    if (Test-Path -LiteralPath $PDF) { Remove-Item -LiteralPath $PDF -Force }
    $pres.SaveAs($OUT, 24)
    $pres.SaveAs($PDF, 32)
    New-Item -ItemType Directory -Force -Path $RENDER | Out-Null
    Get-ChildItem -LiteralPath $RENDER -File -ErrorAction SilentlyContinue | Remove-Item -Force
    $pres.Export($RENDER, 'PNG', 1600, 900)
    Write-Output "PPTX=$OUT"
    Write-Output "PDF=$PDF"
    Write-Output "Slides=$($pres.Slides.Count)"
}
finally {
    if ($pres) { $pres.Close() }
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($pres) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
