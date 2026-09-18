import 'dart:async';

import 'package:flutter/material.dart';

class AppBackground extends StatefulWidget {
  final Widget child;

  const AppBackground({super.key, required this.child});

  @override
  State<AppBackground> createState() => _AppBackgroundState();
}

class _AppBackgroundState extends State<AppBackground> {
  static const _images = [
    'assets/img/code2.png',
    'assets/img/code3.png',
    'assets/img/code4.jpg',
  ];
  int _index = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 8), (_) {
      if (mounted) setState(() => _index = (_index + 1) % _images.length);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 900),
          child: Transform.translate(
            key: ValueKey(_index),
            offset: const Offset(0, -26),
            child: Transform.scale(
              scale: 1.05,
              child: Image.asset(
                _images[_index],
                fit: BoxFit.cover,
                width: double.infinity,
                height: double.infinity,
              ),
            ),
          ),
        ),
        Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color.fromRGBO(255, 126, 0, 0.78),
                Color.fromRGBO(255, 126, 0, 0.22),
                Color.fromRGBO(20, 76, 48, 0.72),
              ],
            ),
          ),
        ),
        Align(
          alignment: const Alignment(0, -0.72),
          child: Opacity(
            opacity: 0.24,
            child: Image.asset(
              'assets/img/armoirie1.png',
              width: 180,
              height: 180,
              fit: BoxFit.contain,
            ),
          ),
        ),
        widget.child,
      ],
    );
  }
}
