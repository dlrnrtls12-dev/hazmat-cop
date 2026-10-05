import olefile
import zlib
import os
import struct

def parse_hwp_text(filepath):
    if not os.path.exists(filepath):
        return f"File not found: {filepath}"
    try:
        ole = olefile.OleFileIO(filepath)
    except Exception as e:
        return f"Error opening ole: {e}"
    
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
            level = (header >> 10) & 0x3FF
            size = (header >> 20) & 0xFFF
            offset += 4
            if size == 0xFFF:
                if offset + 4 > len(data):
                    break
                size = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
            
            record_data = data[offset:offset+size]
            offset += size
            
            # HWPTAG_PARA_TEXT = 67
            if tag_id == 67:
                text_chars = []
                idx = 0
                while idx < len(record_data) - 1:
                    code = record_data[idx] | (record_data[idx+1] << 8)
                    idx += 2
                    if code in (10, 13):
                        text_chars.append('\n')
                    elif code < 32:
                        # control characters
                        if code in (1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23):
                            idx += 14  # skip extended control
                        elif code in (4, 5, 6, 7, 8, 9, 19, 20):
                            pass
                        elif code in (24, 25, 26, 27, 28, 29, 30, 31):
                            pass
                    else:
                        text_chars.append(chr(code))
                full_text.append(''.join(text_chars))
    
    return '\n'.join(full_text)

desktop = r'c:\Users\이국신\Desktop'
files = [
    '공공데이터포털 api.hwp',
    'lawapi.hwp',
    '브이월드 api.hwp',
    '빅데이터 api.hwp',
    'gemini api.hwp',
    '오픈ai api.hwp'
]

out_lines = []
for fn in files:
    fp = os.path.join(desktop, fn)
    out_lines.append(f"==================== {fn} ====================")
    text = parse_hwp_text(fp)
    out_lines.append(text)
    out_lines.append("\n\n")

with open("desktop_apis_extracted.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(out_lines))

print("Extracted successfully to desktop_apis_extracted.txt")
