import time
import hashlib
import os
import magic
import logging
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to prevent abuse"""
    
    def __init__(self, max_requests=5, time_window=3600):  # 5 requests per hour
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip):
        """Check if client IP is allowed to make a request"""
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[client_ip]) < self.max_requests:
            self.requests[client_ip].append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, client_ip):
        """Get remaining requests for client IP"""
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.time_window
        ]
        
        return max(0, self.max_requests - len(self.requests[client_ip]))
    
    def get_reset_time(self, client_ip):
        """Get time when rate limit resets for client IP"""
        if not self.requests[client_ip]:
            return 0
        
        oldest_request = min(self.requests[client_ip])
        return oldest_request + self.time_window

class SecurityValidator:
    """Security validator for uploaded files"""
    
    def __init__(self):
        # Allowed file extensions
        self.allowed_extensions = {'.fbx', '.FBX'}
        
        # Maximum file size (100MB)
        self.max_file_size = 100 * 1024 * 1024
        
        # Minimum file size (1KB)
        self.min_file_size = 1024
        
        # Dangerous file patterns to check for
        self.dangerous_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'data:text/html',
            b'<?php',
            b'<%',
            b'exec(',
            b'system(',
            b'shell_exec(',
            b'passthru(',
            b'eval(',
            b'assert(',
            b'file_get_contents(',
            b'file_put_contents(',
            b'fopen(',
            b'fwrite(',
            b'include(',
            b'require(',
        ]
    
    def validate_file(self, file):
        """Validate uploaded file for security and format"""
        try:
            # Check if file object is valid
            if not file or not hasattr(file, 'filename') or not file.filename:
                logger.warning("Invalid file object")
                return False
            
            # Check file extension
            if not self._validate_extension(file.filename):
                logger.warning(f"Invalid file extension: {file.filename}")
                return False
            
            # Read file content for validation
            file.seek(0)
            content = file.read()
            file.seek(0)  # Reset file pointer
            
            # Check file size
            if not self._validate_file_size(content):
                logger.warning(f"Invalid file size: {len(content)} bytes")
                return False
            
            # Check MIME type
            if not self._validate_mime_type(content):
                logger.warning("Invalid MIME type")
                return False
            
            # Check for dangerous patterns
            if not self._validate_content_safety(content):
                logger.warning("Potentially dangerous content detected")
                return False
            
            # Validate FBX file structure
            if not self._validate_fbx_structure(content):
                logger.warning("Invalid FBX file structure")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False
    
    def _validate_extension(self, filename):
        """Validate file extension"""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.allowed_extensions
    
    def _validate_file_size(self, content):
        """Validate file size"""
        size = len(content)
        return self.min_file_size <= size <= self.max_file_size
    
    def _validate_mime_type(self, content):
        """Validate MIME type using python-magic"""
        try:
            # Try to detect MIME type
            mime_type = magic.from_buffer(content, mime=True)
            
            # FBX files are typically detected as application/octet-stream
            # or might not be recognized by magic
            allowed_mime_types = {
                'application/octet-stream',
                'application/x-fbx',
                'model/fbx',
                'application/fbx'
            }
            
            return mime_type in allowed_mime_types or mime_type.startswith('application/')
            
        except Exception as e:
            logger.warning(f"MIME type detection failed: {str(e)}")
            # If magic fails, continue with other validations
            return True
    
    def _validate_content_safety(self, content):
        """Check for dangerous patterns in file content"""
        content_lower = content.lower()
        
        for pattern in self.dangerous_patterns:
            if pattern in content_lower:
                return False
        
        return True
    
    def _validate_fbx_structure(self, content):
        """Basic FBX file structure validation"""
        try:
            # FBX files should start with specific magic bytes
            # Binary FBX files start with "Kaydara FBX Binary"
            # ASCII FBX files start with "; FBX"
            
            if content.startswith(b'Kaydara FBX Binary'):
                return self._validate_binary_fbx(content)
            elif content.startswith(b'; FBX') or b'FBXHeaderExtension' in content[:1024]:
                return self._validate_ascii_fbx(content)
            else:
                logger.warning("File doesn't appear to be a valid FBX file")
                return False
                
        except Exception as e:
            logger.warning(f"FBX structure validation failed: {str(e)}")
            return False
    
    def _validate_binary_fbx(self, content):
        """Validate binary FBX file structure"""
        try:
            # Check minimum length for binary FBX
            if len(content) < 32:
                return False
            
            # Check magic header
            if not content.startswith(b'Kaydara FBX Binary'):
                return False
            
            # Check version number exists (after magic header)
            if len(content) < 27:
                return False
            
            # Basic structural check - binary FBX should have certain patterns
            return True
            
        except Exception as e:
            logger.warning(f"Binary FBX validation failed: {str(e)}")
            return False
    
    def _validate_ascii_fbx(self, content):
        """Validate ASCII FBX file structure"""
        try:
            # Try to decode as text
            text_content = content.decode('utf-8', errors='ignore')
            
            # Check for required FBX elements
            required_elements = [
                'FBXHeaderExtension',
                'FBXVersion',
                'Definitions',
                'Objects'
            ]
            
            for element in required_elements:
                if element not in text_content:
                    logger.warning(f"Missing required FBX element: {element}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"ASCII FBX validation failed: {str(e)}")
            return False

class FileHasher:
    """Utility for generating file hashes"""
    
    @staticmethod
    def get_file_hash(file_content, algorithm='sha256'):
        """Generate hash for file content"""
        hasher = hashlib.new(algorithm)
        hasher.update(file_content)
        return hasher.hexdigest()
    
    @staticmethod
    def get_file_info(file_content, filename):
        """Get comprehensive file information"""
        return {
            'filename': filename,
            'size': len(file_content),
            'sha256': FileHasher.get_file_hash(file_content, 'sha256'),
            'md5': FileHasher.get_file_hash(file_content, 'md5'),
            'timestamp': datetime.now().isoformat()
        }

class SandboxValidator:
    """Additional sandbox validation utilities"""
    
    @staticmethod
    def validate_filename(filename):
        """Validate filename for security"""
        # Remove any path traversal attempts
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for dangerous characters
        if not all(c in safe_chars for c in filename):
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe storage"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace dangerous characters
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
        sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
        
        # Ensure it doesn't start with a dot
        if sanitized.startswith('.'):
            sanitized = 'file_' + sanitized
        
        # Limit length
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:95] + ext
        
        return sanitized

class LoggingUtility:
    """Centralized logging utilities"""
    
    @staticmethod
    def log_conversion_start(job_id, filename, client_ip):
        """Log conversion start"""
        logger.info(f"Conversion started - Job: {job_id}, File: {filename}, IP: {client_ip}")
    
    @staticmethod
    def log_conversion_end(job_id, success, error_msg=None):
        """Log conversion end"""
        status = "SUCCESS" if success else "FAILED"
        if error_msg:
            logger.info(f"Conversion {status} - Job: {job_id}, Error: {error_msg}")
        else:
            logger.info(f"Conversion {status} - Job: {job_id}")
    
    @staticmethod
    def log_security_violation(violation_type, details, client_ip):
        """Log security violations"""
        logger.warning(f"SECURITY: {violation_type} - Details: {details}, IP: {client_ip}")
    
    @staticmethod
    def log_rate_limit_hit(client_ip, remaining_time):
        """Log rate limit violations"""
        logger.warning(f"RATE_LIMIT: IP {client_ip} hit rate limit, reset in {remaining_time}s")