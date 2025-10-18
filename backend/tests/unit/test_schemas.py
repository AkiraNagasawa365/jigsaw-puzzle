"""
Pydantic schemasのバリデーションテスト

今日実装したInput validationのセキュリティ対策を検証します：
1. pieceCount: 厳密な値リストへの限定
2. puzzleName: XSS対策（HTMLタグ、制御文字の拒否）
3. fileName: パストラバーサル対策、不正文字の拒否、拡張子チェック
4. userId: 最大長制限

テストカバレッジ: 正常系 + 異常系 + エッジケース
"""

import pytest
from pydantic import ValidationError
from app.core.schemas import (
    PuzzleCreateRequest,
    PuzzleCreateResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    ErrorResponse
)


# ===================================================================
# PuzzleCreateRequest のテスト
# ===================================================================

class TestPuzzleCreateRequest:
    """
    パズル作成リクエストのバリデーションテスト

    検証項目:
    - pieceCount: 有効な値リスト [100, 300, 500, 1000, 2000]
    - puzzleName: XSS対策、文字列長、トリミング
    - userId: 最大長制限
    """

    # ========== pieceCount のテスト ==========

    @pytest.mark.unit
    @pytest.mark.validation
    def test_valid_piece_counts(self):
        """
        正常系: 有効なpieceCountの値を全てテスト

        検証: [100, 300, 500, 1000, 2000] が全て受け入れられる
        """
        valid_counts = [100, 300, 500, 1000, 2000]

        for count in valid_counts:
            request = PuzzleCreateRequest(
                puzzleName="Test Puzzle",
                pieceCount=count,
                userId="test-user"
            )
            assert request.pieceCount == count, \
                f"pieceCount={count} should be valid"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_invalid_piece_count_below_minimum(self):
        """
        異常系: 最小値未満のpieceCountを拒否

        検証: 99以下の値がValidationErrorになる
        """
        invalid_counts = [0, 1, 50, 99]

        for count in invalid_counts:
            with pytest.raises(ValidationError) as exc_info:
                PuzzleCreateRequest(
                    puzzleName="Test",
                    pieceCount=count
                )
            # エラーメッセージにpieceCountが含まれることを確認
            error_dict = exc_info.value.errors()[0]
            assert 'pieceCount' in str(error_dict['loc']), \
                f"pieceCount={count} should raise validation error"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_invalid_piece_count_between_valid_values(self):
        """
        異常系: 有効な値の間の値を拒否

        検証: 150, 250, 750など中間値がValidationErrorになる
        重要: Literal型により、リストに無い値は全て拒否される
        """
        invalid_counts = [150, 250, 400, 600, 750, 1500]

        for count in invalid_counts:
            with pytest.raises(ValidationError) as exc_info:
                PuzzleCreateRequest(
                    puzzleName="Test",
                    pieceCount=count
                )
            error_dict = exc_info.value.errors()[0]
            assert 'pieceCount' in str(error_dict['loc']), \
                f"pieceCount={count} (between valid values) should be rejected"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_invalid_piece_count_above_maximum(self):
        """
        異常系: 最大値を超えるpieceCountを拒否

        検証: 2001以上の値がValidationErrorになる
        """
        invalid_counts = [2001, 3000, 5000, 10000]

        for count in invalid_counts:
            with pytest.raises(ValidationError) as exc_info:
                PuzzleCreateRequest(
                    puzzleName="Test",
                    pieceCount=count
                )
            error_dict = exc_info.value.errors()[0]
            assert 'pieceCount' in str(error_dict['loc']), \
                f"pieceCount={count} should be rejected"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_invalid_piece_count_negative(self):
        """
        異常系: 負の値を拒否

        検証: マイナスの値がValidationErrorになる
        """
        with pytest.raises(ValidationError):
            PuzzleCreateRequest(
                puzzleName="Test",
                pieceCount=-100
            )

    # ========== puzzleName のテスト ==========

    @pytest.mark.unit
    @pytest.mark.validation
    def test_valid_puzzle_name(self):
        """
        正常系: 有効なパズル名

        検証: 通常の文字列が受け入れられる
        """
        valid_names = [
            "富士山の風景",
            "My Favorite Puzzle",
            "Test 123",
            "Puzzle-Name_2024",
            "パズル名前",
            "日本語・English・123"
        ]

        for name in valid_names:
            request = PuzzleCreateRequest(
                puzzleName=name,
                pieceCount=300
            )
            assert request.puzzleName == name.strip(), \
                f"puzzleName='{name}' should be valid"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_puzzle_name_xss_prevention_script_tags(self, xss_attack_payloads):
        """
        セキュリティテスト: XSS攻撃（scriptタグ）を防止

        検証: <script>を含む文字列が拒否される
        重要: 実際のXSS攻撃パターンを使用
        """
        script_payloads = [p for p in xss_attack_payloads if '<script' in p.lower()]

        for payload in script_payloads:
            with pytest.raises(ValidationError) as exc_info:
                PuzzleCreateRequest(
                    puzzleName=payload,
                    pieceCount=300
                )
            # エラーメッセージに「HTML tags」が含まれることを確認
            assert 'HTML tags' in str(exc_info.value), \
                f"XSS payload should be blocked: {payload}"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_puzzle_name_xss_prevention_all_html_tags(self, xss_attack_payloads):
        """
        セキュリティテスト: < または > を含む文字列を拒否

        検証: HTMLタグの記号 <> を含む全ての文字列が拒否される
        注意: javascript: などのプロトコルハンドラーは < > が無いため通過する
              (さらに厳密な対策が必要な場合は別途実装)
        """
        # < または > を含むペイロードのみテスト
        html_tag_payloads = [p for p in xss_attack_payloads if '<' in p or '>' in p]

        for payload in html_tag_payloads:
            with pytest.raises(ValidationError) as exc_info:
                PuzzleCreateRequest(
                    puzzleName=payload,
                    pieceCount=300
                )
            error_message = str(exc_info.value)
            assert 'HTML tags' in error_message, \
                f"HTML tags should be blocked: {payload}"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_puzzle_name_control_characters(self):
        """
        セキュリティテスト: 制御文字を拒否

        検証: Null byte、改行、タブなどの制御文字が拒否される
        重要: データベースインジェクションやログ汚染を防ぐ
        """
        control_char_names = [
            "Test\x00Puzzle",  # Null byte
            "Test\x01Name",    # SOH (Start of Heading)
            "Test\x02File",    # STX (Start of Text)
            "Puzzle\x1fName",  # US (Unit Separator)
        ]

        for name in control_char_names:
            with pytest.raises(ValidationError) as exc_info:
                PuzzleCreateRequest(
                    puzzleName=name,
                    pieceCount=300
                )
            assert 'control characters' in str(exc_info.value).lower(), \
                f"Control characters should be blocked: {repr(name)}"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_puzzle_name_trimming(self):
        """
        正常系: パズル名の前後の空白を自動削除

        検証: strip()処理が正しく動作する
        注意: タブ(\t)や改行(\n)は制御文字なので別途拒否される
        """
        names_with_whitespace = [
            ("  富士山  ", "富士山"),
            ("  Spaces Around  ", "Spaces Around"),
            ("   Test   ", "Test"),
        ]

        for input_name, expected_output in names_with_whitespace:
            request = PuzzleCreateRequest(
                puzzleName=input_name,
                pieceCount=300
            )
            assert request.puzzleName == expected_output, \
                f"'{input_name}' should be trimmed to '{expected_output}'"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_puzzle_name_min_length(self):
        """
        異常系: 最小長違反（空文字列）

        検証: 空文字列が拒否される
        """
        with pytest.raises(ValidationError) as exc_info:
            PuzzleCreateRequest(
                puzzleName="",
                pieceCount=300
            )
        assert 'puzzleName' in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.validation
    def test_puzzle_name_max_length(self):
        """
        異常系: 最大長違反（101文字以上）

        検証: 100文字を超える文字列が拒否される
        """
        # 101文字の文字列
        too_long_name = "a" * 101

        with pytest.raises(ValidationError) as exc_info:
            PuzzleCreateRequest(
                puzzleName=too_long_name,
                pieceCount=300
            )
        assert 'puzzleName' in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.validation
    def test_puzzle_name_exact_max_length(self):
        """
        境界値テスト: 最大長ちょうど（100文字）

        検証: 100文字は有効
        """
        exactly_100_chars = "a" * 100

        request = PuzzleCreateRequest(
            puzzleName=exactly_100_chars,
            pieceCount=300
        )
        assert len(request.puzzleName) == 100

    # ========== userId のテスト ==========

    @pytest.mark.unit
    @pytest.mark.validation
    def test_user_id_default_value(self):
        """
        正常系: userIdのデフォルト値

        検証: userIdを指定しない場合、"anonymous"になる
        """
        request = PuzzleCreateRequest(
            puzzleName="Test",
            pieceCount=300
        )
        assert request.userId == "anonymous"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_user_id_custom_value(self):
        """
        正常系: カスタムuserId

        検証: 任意のuserIdが設定できる
        """
        request = PuzzleCreateRequest(
            puzzleName="Test",
            pieceCount=300,
            userId="user-12345"
        )
        assert request.userId == "user-12345"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_user_id_max_length(self):
        """
        異常系: userId最大長違反

        検証: 50文字を超えるuserIdが拒否される
        """
        too_long_user_id = "u" * 51

        with pytest.raises(ValidationError) as exc_info:
            PuzzleCreateRequest(
                puzzleName="Test",
                pieceCount=300,
                userId=too_long_user_id
            )
        assert 'userId' in str(exc_info.value)


# ===================================================================
# UploadUrlRequest のテスト
# ===================================================================

class TestUploadUrlRequest:
    """
    画像アップロードURLリクエストのバリデーションテスト

    検証項目:
    - fileName: パストラバーサル対策、不正文字拒否、拡張子チェック
    - userId: 最大長制限
    """

    # ========== fileName 正常系 ==========

    @pytest.mark.unit
    @pytest.mark.validation
    def test_valid_file_extensions_jpg(self):
        """
        正常系: .jpg拡張子

        検証: .jpg ファイルが受け入れられる
        """
        valid_filenames = [
            "puzzle.jpg",
            "image.jpg",
            "photo123.jpg",
            "my-puzzle_final.jpg"
        ]

        for filename in valid_filenames:
            request = UploadUrlRequest(fileName=filename)
            assert request.fileName == filename

    @pytest.mark.unit
    @pytest.mark.validation
    def test_valid_file_extensions_jpeg(self):
        """
        正常系: .jpeg拡張子

        検証: .jpeg ファイルが受け入れられる
        """
        valid_filenames = [
            "puzzle.jpeg",
            "image.jpeg",
            "photo.jpeg"
        ]

        for filename in valid_filenames:
            request = UploadUrlRequest(fileName=filename)
            assert request.fileName == filename

    @pytest.mark.unit
    @pytest.mark.validation
    def test_valid_file_extensions_png(self):
        """
        正常系: .png拡張子

        検証: .png ファイルが受け入れられる
        """
        valid_filenames = [
            "puzzle.png",
            "image.png",
            "screenshot.png"
        ]

        for filename in valid_filenames:
            request = UploadUrlRequest(fileName=filename)
            assert request.fileName == filename

    @pytest.mark.unit
    @pytest.mark.validation
    def test_valid_file_extensions_case_insensitive(self):
        """
        正常系: 大文字小文字の混在

        検証: JPG, Jpg, jPg など大文字小文字が混在しても有効
        """
        case_variations = [
            "PHOTO.JPG",
            "Image.Jpeg",
            "puzzle.PNG",
            "test.JpG",
            "file.PnG"
        ]

        for filename in case_variations:
            request = UploadUrlRequest(fileName=filename)
            assert request.fileName == filename, \
                f"'{filename}' should be valid (case-insensitive)"

    # ========== fileName 異常系: 拡張子 ==========

    @pytest.mark.unit
    @pytest.mark.validation
    def test_invalid_file_extensions(self):
        """
        異常系: 許可されていない拡張子を拒否

        検証: jpg, jpeg, png 以外の拡張子が拒否される
        重要: セキュリティリスクのあるファイルをブロック
        """
        invalid_filenames = [
            "file.gif",
            "image.bmp",
            "photo.tiff",
            "document.pdf",
            "script.js",
            "executable.exe",
            "archive.zip",
            "video.mp4",
            "malware.bat",
            "code.py"
        ]

        for filename in invalid_filenames:
            with pytest.raises(ValidationError) as exc_info:
                UploadUrlRequest(fileName=filename)
            error_message = str(exc_info.value).lower()
            assert 'extension' in error_message, \
                f"'{filename}' should be rejected (invalid extension)"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_filename_without_extension(self):
        """
        異常系: 拡張子なしのファイル名を拒否

        検証: 拡張子のないファイル名が拒否される
        """
        with pytest.raises(ValidationError):
            UploadUrlRequest(fileName="noextension")

    # ========== fileName セキュリティ: パストラバーサル ==========

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_path_traversal_prevention_unix(self, path_traversal_payloads):
        """
        セキュリティテスト: パストラバーサル攻撃を防止（Unix形式）

        検証: ../ を含むパスが全て拒否される
        重要: サーバーの機密ファイルへのアクセスを防ぐ
        """
        unix_payloads = [p for p in path_traversal_payloads if '../' in p]

        for payload in unix_payloads:
            with pytest.raises(ValidationError) as exc_info:
                UploadUrlRequest(fileName=payload)
            error_message = str(exc_info.value).lower()
            assert 'path traversal' in error_message, \
                f"Unix path traversal should be blocked: {payload}"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_path_traversal_prevention_windows(self, path_traversal_payloads):
        """
        セキュリティテスト: パストラバーサル攻撃を防止（Windows形式）

        検証: ..\\ を含むパスが全て拒否される
        """
        windows_payloads = [p for p in path_traversal_payloads if '..\\' in p]

        for payload in windows_payloads:
            with pytest.raises(ValidationError) as exc_info:
                UploadUrlRequest(fileName=payload)
            error_message = str(exc_info.value).lower()
            assert 'path traversal' in error_message, \
                f"Windows path traversal should be blocked: {payload}"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_path_traversal_prevention_dot_dot(self):
        """
        セキュリティテスト: .. 自体を拒否

        検証: ファイル名に .. が含まれるだけで拒否される
        """
        with pytest.raises(ValidationError) as exc_info:
            UploadUrlRequest(fileName="file..jpg")
        assert 'path traversal' in str(exc_info.value).lower()

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_path_with_forward_slash(self):
        """
        セキュリティテスト: スラッシュ（/）を拒否

        検証: ディレクトリ区切り文字が拒否される
        """
        filenames_with_slash = [
            "dir/file.jpg",
            "folder/subfolder/image.png",
            "/absolute/path.jpeg"
        ]

        for filename in filenames_with_slash:
            with pytest.raises(ValidationError) as exc_info:
                UploadUrlRequest(fileName=filename)
            assert 'path traversal' in str(exc_info.value).lower(), \
                f"Forward slash should be blocked: {filename}"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_path_with_backslash(self):
        """
        セキュリティテスト: バックスラッシュ（\\）を拒否

        検証: Windows形式のパス区切りが拒否される
        """
        filenames_with_backslash = [
            "dir\\file.jpg",
            "folder\\image.png",
            "C:\\path\\to\\file.jpeg"
        ]

        for filename in filenames_with_backslash:
            with pytest.raises(ValidationError) as exc_info:
                UploadUrlRequest(fileName=filename)
            assert 'path traversal' in str(exc_info.value).lower(), \
                f"Backslash should be blocked: {filename}"

    # ========== fileName セキュリティ: 不正文字 ==========

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_invalid_characters_in_filename(self, invalid_filename_chars):
        """
        セキュリティテスト: ファイル名として不正な文字を拒否

        検証: <, >, :, ", |, ?, * や制御文字が拒否される
        重要: OSレベルのファイルシステムエラーを防ぐ
        """
        for filename in invalid_filename_chars:
            with pytest.raises(ValidationError) as exc_info:
                UploadUrlRequest(fileName=filename)
            error_message = str(exc_info.value).lower()
            # 制御文字の場合は "control characters" 、それ以外は "invalid characters"
            assert ('invalid characters' in error_message or 'control characters' in error_message), \
                f"Invalid character should be blocked: {filename}"

    @pytest.mark.unit
    @pytest.mark.validation
    @pytest.mark.security
    def test_filename_control_characters(self):
        """
        セキュリティテスト: 制御文字を含むファイル名を拒否

        検証: Null byte、改行などの制御文字が拒否される
        """
        control_char_filenames = [
            "null\x00byte.jpg",
            "tab\ttab.png",
            "newline\nhere.jpeg",
            "control\x01char.jpg"
        ]

        for filename in control_char_filenames:
            with pytest.raises(ValidationError) as exc_info:
                UploadUrlRequest(fileName=filename)
            assert 'control characters' in str(exc_info.value).lower(), \
                f"Control characters should be blocked: {repr(filename)}"

    # ========== fileName その他 ==========

    @pytest.mark.unit
    @pytest.mark.validation
    def test_filename_trimming(self):
        """
        正常系: ファイル名の前後の空白を自動削除

        検証: strip()処理が正しく動作する
        注意: タブ(\t)は制御文字なので別途拒否される
        """
        filenames_with_whitespace = [
            ("  puzzle.jpg  ", "puzzle.jpg"),
            ("  photo.jpeg  ", "photo.jpeg"),
            ("   image.png   ", "image.png"),
        ]

        for input_filename, expected_output in filenames_with_whitespace:
            request = UploadUrlRequest(fileName=input_filename)
            assert request.fileName == expected_output, \
                f"'{input_filename}' should be trimmed to '{expected_output}'"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_filename_max_length(self):
        """
        異常系: ファイル名最大長違反

        検証: 255文字を超えるファイル名が拒否される
        """
        # 256文字のファイル名（拡張子含む）
        too_long_filename = "a" * 252 + ".jpg"  # 252 + 4 = 256文字

        with pytest.raises(ValidationError) as exc_info:
            UploadUrlRequest(fileName=too_long_filename)
        assert 'fileName' in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.validation
    def test_filename_default_value(self):
        """
        正常系: fileNameのデフォルト値

        検証: fileNameを指定しない場合、"puzzle.jpg"になる
        """
        request = UploadUrlRequest()
        assert request.fileName == "puzzle.jpg"

    # ========== userId のテスト ==========

    @pytest.mark.unit
    @pytest.mark.validation
    def test_upload_user_id_default(self):
        """
        正常系: userIdのデフォルト値

        検証: userIdを指定しない場合、"anonymous"になる
        """
        request = UploadUrlRequest(fileName="test.jpg")
        assert request.userId == "anonymous"

    @pytest.mark.unit
    @pytest.mark.validation
    def test_upload_user_id_max_length(self):
        """
        異常系: userId最大長違反

        検証: 50文字を超えるuserIdが拒否される
        """
        too_long_user_id = "u" * 51

        with pytest.raises(ValidationError) as exc_info:
            UploadUrlRequest(
                fileName="test.jpg",
                userId=too_long_user_id
            )
        assert 'userId' in str(exc_info.value)


# ===================================================================
# レスポンススキーマのテスト
# ===================================================================

class TestResponseSchemas:
    """
    レスポンススキーマの基本的なテスト

    検証項目: 各フィールドが正しく設定できることを確認
    """

    @pytest.mark.unit
    def test_puzzle_create_response(self):
        """PuzzleCreateResponseの正常系"""
        response = PuzzleCreateResponse(
            puzzleId="test-id",
            puzzleName="Test Puzzle",
            pieceCount=300,
            status="pending",
            message="Success"
        )
        assert response.puzzleId == "test-id"
        assert response.pieceCount == 300

    @pytest.mark.unit
    def test_upload_url_response(self):
        """UploadUrlResponseの正常系"""
        response = UploadUrlResponse(
            puzzleId="test-id",
            uploadUrl="https://example.com/upload",
            expiresIn=900,
            message="URL generated"
        )
        assert response.expiresIn == 900

    @pytest.mark.unit
    def test_error_response(self):
        """ErrorResponseの正常系"""
        response = ErrorResponse(
            error="Test error",
            details="Detailed message"
        )
        assert response.error == "Test error"
        assert response.details == "Detailed message"

    @pytest.mark.unit
    def test_error_response_without_details(self):
        """ErrorResponseのdetailsはoptional"""
        response = ErrorResponse(error="Test error")
        assert response.details is None
