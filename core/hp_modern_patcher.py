import os
import re

class HPModernPasswordPatcher:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.bios_data = None
        self.file_size = 0
        self.is_loaded = False
        
        self._load_file()

        # Signatures for Modern HP (6th Gen and above NVRAM / VSS blocks)
        self.security_signatures = {
            "HP_VSS_Block": b'H\x00P\x00Q\x00F\x00l\x00a\x00s\x00h',
            # You can add alternative HP security strings here based on HxD findings
        }

    def _load_file(self):
        try:
            with open(self.file_path, 'rb') as f:
                self.bios_data = bytearray(f.read())
            self.file_size = len(self.bios_data)
            self.is_loaded = True
        except Exception as e:
            self.is_loaded = False
            self.error_msg = f"Failed to load file: {str(e)}"

    def _is_payload_empty(self, payload_data):
        """Checks if the targeted data block is already clean."""
        if all(b == 0xFF for b in payload_data) or all(b == 0x00 for b in payload_data):
            return True
        return False

    def scan_file(self):
        if not self.is_loaded:
            return {"status": "error", "message": self.error_msg}

        found_blocks = []
        payload_length = 128  # Block size to clear upon match

        for name, pattern in self.security_signatures.items():
            matches = [m.start() for m in re.finditer(re.escape(pattern), self.bios_data)]
            for offset in matches:
                signature_len = len(pattern)
                # Offset adjustment for HP NVRAM structure
                payload_start = offset + signature_len + 16
                
                if payload_start + payload_length <= self.file_size:
                    payload_data = self.bios_data[payload_start:payload_start + payload_length]
                    
                    if not self._is_payload_empty(payload_data):
                        found_blocks.append({
                            "name": name,
                            "offset": offset,
                            "payload_start": payload_start
                        })

        if not found_blocks:
            return {
                "status": "clean", 
                "message": "No active HP password flags detected. File is already clean or uses a different structure."
            }

        return {
            "status": "locked",
            "message": f"Active HP password data found in {len(found_blocks)} location(s).",
            "blocks": found_blocks
        }

    def apply_patch(self, blocks_to_patch, payload_length=128):
        if not self.is_loaded:
            return False, "File is not loaded properly."

        patches_applied = 0

        for block in blocks_to_patch:
            payload_start = block["payload_start"]
            
            if payload_start + payload_length <= self.file_size:
                for i in range(payload_start, payload_start + payload_length):
                    self.bios_data[i] = 0xFF
                patches_applied += 1

        if patches_applied > 0:
            return self._save_file()
        else:
            return False, "Failed to apply HP patches."

    def _save_file(self):
        name, ext = os.path.splitext(self.file_path)
        output_file = f"{name}_hp_unlocked{ext}"
        
        try:
            with open(output_file, 'wb') as f:
                f.write(self.bios_data)
            return True, f"Success! HP Password cleared. File saved as:\n{output_file}"
        except Exception as e:
            return False, f"Error saving file: {str(e)}"

    def auto_scan_and_remove(self):
        if not self.is_loaded:
            return "Error", "File could not be loaded."

        scan_result = self.scan_file()

        if scan_result["status"] == "clean":
            return "Clean", scan_result["message"]
        
        elif scan_result["status"] == "locked":
            blocks = scan_result["blocks"]
            success, save_message = self.apply_patch(blocks)
            
            if success:
                return "Success", save_message
            else:
                return "Error", save_message
        else:
            return "Error", scan_result.get("message", "Unknown error during scan.")