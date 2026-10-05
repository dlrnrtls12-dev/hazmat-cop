import os
import re
import sys
import json
import zlib
import struct
import zipfile
import xml.etree.ElementTree as ET
import olefile
from pypdf import PdfReader

sys.stdout.reconfigure(encoding='utf-8')

def parse_hwp(filepath):
    try:
        ole = olefile.OleFileIO(filepath)
        sections = [s for s in ole.listdir() if s[0] == 'BodyText']
        sections.sort()
        full_text = []
        for sec in sections:
            stream = ole.openstream(sec)
            data = stream.read()
            try:
                data = zlib.decompress(data, -15)
            except Exception:
                pass
            
            offset = 0
            while offset < len(data):
                if offset + 4 > len(data):
                    break
                header = struct.unpack('<I', data[offset:offset+4])[0]
                tag_id = header & 0x3FF
                size = (header >> 20) & 0xFFF
                offset += 4
                if size == 0xFFF:
                    if offset + 4 > len(data):
                        break
                    size = struct.unpack('<I', data[offset:offset+4])[0]
                    offset += 4
                record_data = data[offset:offset+size]
                offset += size

                if tag_id == 67: # HWPTAG_PARA_TEXT
                    text_chars = []
                    idx = 0
                    while idx < len(record_data) - 1:
                        code = record_data[idx] | (record_data[idx+1] << 8)
                        idx += 2
                        if code in (10, 13):
                            text_chars.append('\n')
                        elif code < 32:
                            if code in (1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23):
                                idx += 14
                        else:
                            text_chars.append(chr(code))
                    full_text.append(''.join(text_chars))
        return '\n'.join(full_text).strip()
    except Exception as e:
        return f"[HWP Parse Error: {e}]"

def parse_hwpx(filepath):
    try:
        texts = []
        with zipfile.ZipFile(filepath, 'r') as z:
            for name in z.namelist():
                if name.startswith('Contents/section') and name.endswith('.xml'):
                    xml_content = z.read(name)
                    root = ET.fromstring(xml_content)
                    for elem in root.iter():
                        if elem.tag.endswith('}t') and elem.text:
                            texts.append(elem.text)
        return '\n'.join(texts).strip()
    except Exception as e:
        return f"[HWPX Parse Error: {e}]"

def parse_pdf(filepath, max_pages=30):
    try:
        reader = PdfReader(filepath)
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)
        texts = []
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text()
            if page_text:
                texts.append(f"--- [Page {i+1}] ---\n" + page_text.strip())
        return f"(총 {total_pages}페이지 중 주요 {pages_to_read}페이지 추출)\n\n" + '\n\n'.join(texts)
    except Exception as e:
        return f"[PDF Parse Error: {e}]"

def parse_text(filepath):
    for enc in ['utf-8', 'cp949', 'euc-kr']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read().strip()
        except UnicodeDecodeError:
            continue
    return ""

def main():
    target_dir = r"C:\Users\이국신\Desktop\위험물 기획단속 ai"
    if not os.path.exists(target_dir):
        print(f"Directory not found: {target_dir}")
        return

    files = os.listdir(target_dir)
    print(f"Found {len(files)} files in '{target_dir}'")

    knowledge_base = []

    for idx, fname in enumerate(sorted(files), 1):
        fpath = os.path.join(target_dir, fname)
        if os.path.isdir(fpath):
            continue

        ext = os.path.splitext(fname)[1].lower()
        size_kb = round(os.path.getsize(fpath) / 1024, 1)

        doc_type = "기타"
        if re.search(r"^\d+\.", fname):
            doc_type = "소방청 공식 업무지침"
        elif "질의회신" in fname or "질의응답" in fname:
            doc_type = "질의회신 및 해석례"
        elif "수사전략" in fname or "단속" in fname:
            doc_type = "기획단속 수사전략"
        elif "실무해설서" in fname or "매뉴얼" in fname or "요령" in fname:
            doc_type = "위험물 실무해설서 및 매뉴얼"

        print(f"[{idx}/{len(files)}] Parsing ({doc_type}): {fname} ({size_kb} KB)...")

        content = ""
        if ext == '.hwp':
            content = parse_hwp(fpath)
        elif ext == '.hwpx':
            content = parse_hwpx(fpath)
        elif ext == '.pdf':
            content = parse_pdf(fpath, max_pages=25)
        elif ext in ('.txt', '.md'):
            content = parse_text(fpath)
        else:
            content = f"[{ext.upper()} 파일 - 메타데이터만 등록]"

        # 클린징: 공백 및 불필요한 줄바꿈 정리
        cleaned_content = re.sub(r'\n{3,}', '\n\n', content)

        knowledge_base.append({
            "id": f"KB_{idx:03d}",
            "filename": fname,
            "category": doc_type,
            "extension": ext,
            "size_kb": size_kb,
            "char_count": len(cleaned_content),
            "summary_preview": cleaned_content[:300].replace('\n', ' '),
            "content": cleaned_content
        })

    out_json = os.path.join("data", "enforcement_knowledge.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"Knowledge Base Extraction Complete!")
    print(f"Saved {len(knowledge_base)} documents to: {out_json}")
    total_chars = sum(doc['char_count'] for doc in knowledge_base)
    print(f"Total Extracted Characters: {total_chars:,} chars")
    print("=" * 60)

if __name__ == "__main__":
    main()
