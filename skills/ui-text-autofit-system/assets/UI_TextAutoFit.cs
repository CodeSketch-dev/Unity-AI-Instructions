using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Game
{
    // STANDING RULE (docs: AGENTS.md > UI text auto-fit): every TMP text in the game - screen UI, popups, world canvases, text built from code - is normalised
    // the first time it shows or changes, so nobody has to ask for it again:
    //   1. Auto Size ON (min 18 on screen canvases; world canvases keep a proportional min), never a fixed size that can overflow.
    //   2. Single-line labels never wrap and end in an ellipsis instead of spilling out of the rect.
    //   3. Text inside a button / framed panel gets horizontal padding so it never touches the frame or its shadow (vertical offsets are NOT touched).
    // Opt out with UI_TextAutoFitIgnore on the text (tools, debug, intentionally exact sizes). Also run in the Editor on every prefab/scene save (UI_TextAutoFit_Editor).
    public static class UI_TextAutoFit
    {
        public const float SCREEN_MIN_FONT = 18f;
        public const float PAD_X = 12f;
        public const float PAD_FRACTION = 0.08f;

        static readonly HashSet<int> s_done = new HashSet<int>();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetStatics()
        {
            s_done.Clear();
            TMPro_EventManager.TEXT_CHANGED_EVENT.Remove(OnTextChanged);
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterAssembliesLoaded)]
        static void Hook()
        {
            TMPro_EventManager.TEXT_CHANGED_EVENT.Remove(OnTextChanged);
            TMPro_EventManager.TEXT_CHANGED_EVENT.Add(OnTextChanged);
        }

        static void OnTextChanged(Object o)
        {
            if (o is TMP_Text t && t != null && s_done.Add(t.GetInstanceID()))
                Normalize(t);
        }

        /// <summary>Applies the rules to one text. Safe to call repeatedly; returns true when something changed.</summary>
        public static bool Normalize(TMP_Text t, bool? screen = null)
        {
            if (t == null || t.GetComponent<UI_TextAutoFitIgnore>() != null) return false;
            Canvas canvas = t.canvas;
            bool world = screen.HasValue ? !screen.Value : canvas != null && canvas.renderMode == RenderMode.WorldSpace;
            RectTransform rt = t.rectTransform;
            bool changed = false;

            // Hug-content label (rect has no size yet / is driven by a fitter): auto size would collapse it to the minimum font, so leave it alone.
            if (rt.rect.width < 1f || rt.rect.height < 1f) return false;

            if (!t.enableAutoSizing)
            {
                float size = t.fontSize;
                t.fontSizeMax = size;
                t.fontSizeMin = world ? size * 0.5f : Mathf.Min(SCREEN_MIN_FONT, size);
                t.enableAutoSizing = true;
                changed = true;
            }
            else if (!world && t.fontSizeMin < SCREEN_MIN_FONT && t.fontSizeMax > SCREEN_MIN_FONT)
            {
                t.fontSizeMin = SCREEN_MIN_FONT;
                changed = true;
            }

            float width = rt.rect.width;

            bool singleLine = t.textWrappingMode == TextWrappingModes.NoWrap || t.textWrappingMode == TextWrappingModes.PreserveWhitespaceNoWrap;
            if (singleLine && (t.overflowMode == TextOverflowModes.Overflow || t.overflowMode == TextOverflowModes.Truncate))
            {
                t.overflowMode = TextOverflowModes.Ellipsis;
                changed = true;
            }

            if (!world && NeedsCentre(t) && IsSideAligned(t.alignment))
            {
                t.alignment = Centered(t.alignment);
                changed = true;
            }

            if (InFrame(t, width))
            {
                float pad = Mathf.Min(PAD_X, width * PAD_FRACTION);
                Vector4 m = t.margin;
                if (m.x < pad || m.z < pad)
                {
                    t.margin = new Vector4(Mathf.Max(m.x, pad), m.y, Mathf.Max(m.z, pad), m.w);
                    changed = true;
                }
            }
            return changed;
        }

        // Button labels and header titles are always centred.
        static bool NeedsCentre(TMP_Text t)
        {
            Transform p = t.transform.parent;
            if (p != null && p.name == "Header" && t.name.Contains("Title")) return true;
            for (int depth = 0; p != null && depth < 2; depth++, p = p.parent)
                if (p.GetComponent<Selectable>() != null) return true;
            return false;
        }

        static bool IsSideAligned(TextAlignmentOptions a) => ((int)a & (int)HorizontalAlignmentOptions.Left) != 0 || ((int)a & (int)HorizontalAlignmentOptions.Right) != 0;

        static TextAlignmentOptions Centered(TextAlignmentOptions a)
        {
            int vertical = (int)a & 0xFF00;
            return (TextAlignmentOptions)((int)HorizontalAlignmentOptions.Center | vertical);
        }

        // A text that nearly fills a button / framed image: it would touch the frame, so it needs the side padding.
        static bool InFrame(TMP_Text t, float width)
        {
            Transform p = t.transform.parent;
            for (int depth = 0; p != null && depth < 3; depth++, p = p.parent)
            {
                if (p.GetComponent<Selectable>() == null && p.GetComponent<Image>() == null) continue;
                var pr = p as RectTransform;
                if (pr == null) return false;
                float pw = pr.rect.width;
                return pw > 0f && width >= pw * 0.8f;
            }
            return false;
        }
    }

    /// <summary>Put on a TMP text that must keep its exact serialized size / padding (tools, debug, deliberate exceptions).</summary>
    public sealed class UI_TextAutoFitIgnore : MonoBehaviour { }
}
