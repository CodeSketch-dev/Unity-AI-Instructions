using System;
using System.Globalization;

namespace Game
{
    // Idle/simulator style number text: 999, 1.5K, 12.34M, 3B ... Truncates (never rounds up to "1000K").
    public static class NumberFormatter
    {
        static readonly string[] SUFFIXES = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" };

        public static string Format(double value, int maxDecimals = 2)
        {
            if (double.IsNaN(value) || double.IsInfinity(value)) return "0";

            bool negative = value < 0d;
            double scaled = Math.Abs(value);
            string sign = negative ? "-" : "";

            if (scaled < 1000d) return sign + ((long)Math.Floor(scaled)).ToString(CultureInfo.InvariantCulture);

            int index = 0;
            while (scaled >= 1000d && index < SUFFIXES.Length - 1)
            {
                scaled /= 1000d;
                index++;
            }

            // repeated division accumulates error (1e33 -> 999.99999...), so settle it before truncating
            scaled = Math.Round(scaled, 9);
            if (scaled >= 1000d && index < SUFFIXES.Length - 1)
            {
                scaled /= 1000d;
                index++;
            }

            if (scaled >= 1000d) return sign + Math.Abs(value).ToString("0.##e+0", CultureInfo.InvariantCulture);

            double factor = Math.Pow(10d, maxDecimals);
            double truncated = Math.Floor(scaled * factor) / factor;
            string format = maxDecimals > 0 ? "0." + new string('#', maxDecimals) : "0";
            return sign + truncated.ToString(format, CultureInfo.InvariantCulture) + SUFFIXES[index];
        }

        // 45s, 3m 05s, 2h 10m, 3d 4h
        public static string FormatDuration(double seconds)
        {
            long total = (long)Math.Max(0d, Math.Floor(seconds));
            long days = total / 86400;
            long hours = total % 86400 / 3600;
            long minutes = total % 3600 / 60;
            long secs = total % 60;

            if (days > 0) return $"{days}d {hours}h";
            if (hours > 0) return $"{hours}h {minutes:00}m";
            if (minutes > 0) return $"{minutes}m {secs:00}s";
            return $"{secs}s";
        }
    }
}
