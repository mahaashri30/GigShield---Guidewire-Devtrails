import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:gigshield/theme/app_theme.dart';
import 'package:gigshield/providers/app_providers.dart';
import 'package:gigshield/utils/constants.dart';

class ClaimsScreen extends ConsumerWidget {
  const ClaimsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final claimsAsync = ref.watch(claimsProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        title: const Text('Claims History'),
        backgroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: () => ref.invalidate(claimsProvider)),
        ],
      ),
      body: claimsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (claims) => claims.isEmpty
            ? _EmptyState()
            : ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: claims.length,
                itemBuilder: (_, i) => _ClaimCard(claim: claims[i] as Map<String, dynamic>),
              ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.receipt_long_outlined, size: 64, color: AppTheme.textHint),
          const SizedBox(height: 16),
          const Text('No claims yet', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          const Text(
            'Claims are auto-triggered when a\ndisruption event is detected in your area.',
            style: TextStyle(color: AppTheme.textSecondary),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _ClaimCard extends StatelessWidget {
  final Map<String, dynamic> claim;
  const _ClaimCard({required this.claim});

  @override
  Widget build(BuildContext context) {
    final status = claim['status'] as String? ?? 'pending';
    final claimed = (claim['claimed_amount'] as num?)?.toStringAsFixed(0) ?? '0';
    final approved = (claim['approved_amount'] as num?)?.toStringAsFixed(0);
    final dss = ((claim['dss_multiplier'] as num?)?.toDouble() ?? 0) * 100;
    final fraudScore = (claim['fraud_score'] as num?)?.toStringAsFixed(0) ?? '0';
    final autoApproved = claim['auto_approved'] as bool? ?? false;
    final date = claim['created_at'] != null
        ? DateFormat('dd MMM yyyy, hh:mm a').format(DateTime.parse(claim['created_at'] as String))
        : '';

    final statusConfig = {
      'paid': {'color': AppTheme.success, 'icon': Icons.check_circle_rounded, 'label': 'Paid'},
      'approved': {'color': AppTheme.primary, 'icon': Icons.thumb_up_rounded, 'label': 'Approved'},
      'rejected': {'color': AppTheme.danger, 'icon': Icons.cancel_rounded, 'label': 'Rejected'},
      'pending': {'color': AppTheme.warning, 'icon': Icons.pending_rounded, 'label': 'Pending'},
    };
    final sc = statusConfig[status] ?? statusConfig['pending']!;
    final color = sc['color'] as Color;
    final icon = sc['icon'] as IconData;
    final label = sc['label'] as String;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.divider, width: 0.5),
      ),
      child: Column(
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: color, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Claim • $date', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          if (autoApproved)
                            Container(
                              margin: const EdgeInsets.only(right: 6),
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryLight,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text('AI Auto', style: TextStyle(fontSize: 10, color: AppTheme.primary, fontWeight: FontWeight.w600)),
                            ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: color.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(label, style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.w700)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      approved != null ? '₹$approved' : '₹$claimed',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                        color: status == 'rejected' ? AppTheme.danger : AppTheme.primary,
                      ),
                    ),
                    if (status == 'rejected')
                      const Text('Rejected', style: TextStyle(fontSize: 11, color: AppTheme.danger)),
                  ],
                ),
              ],
            ),
          ),

          // Details
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(16),
                bottomRight: Radius.circular(16),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _Detail('DSS', '${dss.toInt()}%'),
                _Detail('Fraud Score', '$fraudScore/100'),
                _Detail('Claimed', '₹$claimed'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Detail extends StatelessWidget {
  final String label, value;
  const _Detail(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11)),
      ],
    );
  }
}
