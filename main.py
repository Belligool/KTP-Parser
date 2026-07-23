import os
import csv
import time
from core.ocr_engine import OCREngine
from core.extractor import KTPExtractor

def main():
    start_time = time.perf_counter()
    target_dir = 'tests/sample_pdfs/'
    
    if not os.path.exists(target_dir):
        print(f"Directory '{target_dir}' not found. Please create it and add KTP PDFs.")
        return
    ocr = OCREngine()
    extractor = KTPExtractor()
    
    all_ktp_records = []
    
    print(f"Starting batch KTP extraction from {target_dir}...\n")
    
    for filename in os.listdir(target_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(target_dir, filename)
            print(f"Scanning: {filename}...")
            raw_text = ocr.extract(pdf_path)
            if filename in ('sue.pdf', 'images.pdf'):
                with open(f'tests/results/{filename}_raw.txt', 'w', encoding='utf-8') as f:
                    f.write(raw_text)
            
            if raw_text:
                parsed_data = extractor.extract_data(raw_text)
                parsed_data['Source File'] = filename
                all_ktp_records.append(parsed_data)
            else:
                print(f"  -> WARNING: No text could be extracted from {filename}")

    # Export to CSV 
    if all_ktp_records:
        output_dir = 'tests/results/'
        os.makedirs(output_dir, exist_ok=True)
        
        csv_filename = os.path.join(output_dir, "ktp_export_results.csv")
        headers = ["Source File", "NIK", "Nama", "Tempat/Tgl Lahir", "Status Pernikahan"]
        
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_ktp_records)
            
        print(f"\n- Woo Yessir -")
        print(f"Exported {len(all_ktp_records)} KTP records to {csv_filename}")
    else:
        print("\nNo KTP data was extracted from the batch.")
    end_time = time.perf_counter()
    execution_time = end_time - start_time

    print(f"Code took {execution_time:.6f} seconds to complete.")

if __name__ == "__main__":
    main()