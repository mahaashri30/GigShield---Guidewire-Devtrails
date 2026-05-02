import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:dio/dio.dart';
import 'dart:io';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class PartnerIDVerificationScreen extends ConsumerStatefulWidget {
  const PartnerIDVerificationScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<PartnerIDVerificationScreen> createState() =>
      _PartnerIDVerificationScreenState();
}

class _PartnerIDVerificationScreenState
    extends ConsumerState<PartnerIDVerificationScreen> {
  File? _selectedImage;
  bool _isLoading = false;
  String? _error;
  final TextEditingController _partnerIdController = TextEditingController();
  final ImagePicker _imagePicker = ImagePicker();
  final storage = const FlutterSecureStorage();

  @override
  void dispose() {
    _partnerIdController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final pickedFile = await _imagePicker.pickImage(source: source);
      if (pickedFile != null) {
        setState(() {
          _selectedImage = File(pickedFile.path);
          _error = null;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to pick image: $e';
      });
    }
  }

  Future<void> _verifyPartnerID() async {
    if (_partnerIdController.text.isEmpty) {
      setState(() => _error = 'Please enter your partner ID');
      return;
    }

    setState(() => _isLoading = true);

    try {
      final token = await storage.read(key: 'auth_token');
      
      final dio = Dio();
      final response = await dio.post(
        'http://16.112.121.102:8000/api/v1/verify/partner-id',
        data: {
          'partner_id': _partnerIdController.text,
          'platform': 'blinkit', // Get from user selection in actual app
        },
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
          contentType: 'application/json',
        ),
      );

      if (response.statusCode == 200) {
        // Navigate to next verification step (selfie)
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Partner ID verified successfully!')),
          );
          // Navigator.push(...) to next screen
        }
      }
    } catch (e) {
      setState(() => _error = 'Verification failed: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Verify Partner ID'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Instruction Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.info, color: Colors.blue),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Verify Your Identity',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Please enter your Partner/Delivery ID and upload a clear photo of your delivery badge.',
                      style: TextStyle(color: Colors.grey, fontSize: 14),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Partner ID Input
            TextField(
              controller: _partnerIdController,
              decoration: InputDecoration(
                labelText: 'Partner ID',
                hintText: 'e.g., DL123456789',
                prefixIcon: const Icon(Icons.badge),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                errorText: _error != null ? '' : null,
              ),
            ),
            const SizedBox(height: 24),

            // Image Selection
            if (_selectedImage == null)
              GestureDetector(
                onTap: () => _showImagePickerDialog(),
                child: Container(
                  height: 200,
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey, width: 2),
                    borderRadius: BorderRadius.circular(12),
                    color: Colors.grey[50],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.cloud_upload, size: 48, color: Colors.grey[400]),
                      const SizedBox(height: 12),
                      Text(
                        'Tap to upload badge photo',
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
              )
            else
              Stack(
                children: [
                  Container(
                    height: 250,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.green, width: 2),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.file(_selectedImage!, fit: BoxFit.cover),
                    ),
                  ),
                  Positioned(
                    top: 8,
                    right: 8,
                    child: FloatingActionButton(
                      mini: true,
                      onPressed: () => setState(() => _selectedImage = null),
                      child: const Icon(Icons.close),
                    ),
                  ),
                  Positioned(
                    bottom: 8,
                    right: 8,
                    child: FloatingActionButton(
                      mini: true,
                      onPressed: () => _showImagePickerDialog(),
                      backgroundColor: Colors.green,
                      child: const Icon(Icons.edit),
                    ),
                  ),
                ],
              ),
            const SizedBox(height: 12),
            if (_selectedImage != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle, color: Colors.green, size: 18),
                    const SizedBox(width: 8),
                    Text(
                      'Badge photo selected',
                      style: TextStyle(color: Colors.green, fontSize: 12),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 24),

            // Error Message
            if (_error != null && _error!.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red[50],
                  border: Border.all(color: Colors.red),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error, color: Colors.red),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _error!,
                        style: const TextStyle(color: Colors.red, fontSize: 14),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 24),

            // Verify Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _verifyPartnerID,
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Verify Partner ID'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showImagePickerDialog() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Take Photo'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.image),
              title: const Text('Choose from Gallery'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }
}
