import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';

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
            ? const _EmptyState()
            : ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: claims.length,
                itemBuilder: (_, i) => _ClaimCard(
                  claim: claims[i] as Map<String, dynamic>,
                  index: i,
                ),
              ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

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

// ── Payout Counter Animation ──────────────────────────────────────────────────
class _AnimatedAmount extends StatefulWidget {
  final double amount;
  final Color color;
  const _AnimatedAmount({required this.amount, required this.color});

  @override
  State<_AnimatedAmount> createState() => _AnimatedAmountState();
}

class _AnimatedAmountState extends State<_AnimatedAmount>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200));
    _anim = Tween<double>(begin: 0, end: widget.amount)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
    _ctrl.forward();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => Text(
        '₹${_anim.value.toStringAsFixed(0)}',
        style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: widget.color),
      ),
    );
  }
}

// ── Claim Card with slide-in + counter ────────────────────────────────────────
class _ClaimCard extends StatefulWidget {
  final Map<String, dynamic> claim;
  final int index;
  const _ClaimCard({required this.claim, required this.index});

  @override
  State<_ClaimCard> createState() => _ClaimCardState();
}

class _ClaimCardState extends State<_ClaimCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<Offset> _slide;
  late Animation<double> _fade;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _slide = Tween<Offset>(begin: const Offset(-0.3, 0), end: Offset.zero)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
    _fade = Tween<double>(begin: 0, end: 1)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeIn));

    // Stagger each card by index
    Future.delayed(Duration(milliseconds: widget.index * 80), () {
      if (mounted) _ctrl.forward();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final claim = widget.claim;
    final status = claim['status'] as String? ?? 'pending';
    final claimed = (claim['claimed_amount'] as num?)?.toDouble() ?? 0;
    final approved = (claim['approved_amount'] as num?)?.toDouble();
    final displayAmount = approved ?? claimed;
    final dss = ((claim['dss_multiplier'] as num?)?.toDouble() ?? 0) * 100;
    final fraudScore = (claim['fraud_score'] as num?)?.toStringAsFixed(0) ?? '0';
    final autoApproved = claim['auto_approved'] as bool? ?? false;
    final date = claim['created_at'] != null
        ? DateFormat('dd MMM yyyy, hh:mm a').format(DateTime.parse(claim['created_at'] as String))
        : '';

    final statusConfig = {
      'paid':     {'color': AppTheme.success, 'icon': Icons.check_circle_rounded, 'label': 'Paid'},
      'approved': {'color': AppTheme.primary,  'icon': Icons.thumb_up_rounded,    'label': 'Approved'},
      'rejected': {'color': AppTheme.danger,   'icon': Icons.cancel_rounded,      'label': 'Rejected'},
      'pending':  {'color': AppTheme.warning,  'icon': Icons.pending_rounded,     'label': 'Pending'},
    };
    final sc = statusConfig[status] ?? statusConfig['pending']!;
    final color = sc['color'] as Color;
    final icon = sc['icon'] as IconData;
    final label = sc['label'] as String;

    return FadeTransition(
      opacity: _fade,
      child: SlideTransition(
        position: _slide,
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.divider, width: 0.5),
          ),
          child: Column(
            children: [
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
                    // Animated payout counter
                    status == 'rejected'
                        ? Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text('₹${claimed.toStringAsFixed(0)}',
                                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppTheme.danger)),
                              const Text('Rejected', style: TextStyle(fontSize: 11, color: AppTheme.danger)),
                            ],
                          )
                        : _AnimatedAmount(amount: displayAmount, color: color),
                  ],
                ),
              ),
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
                    _Detail('Claimed', '₹${claimed.toStringAsFixed(0)}'),
                  ],
                ),
              ),
            ],
          ),
        ),
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
