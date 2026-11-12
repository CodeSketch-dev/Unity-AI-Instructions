#ifndef ROBLOX_BATCHED_SURFACE_INCLUDED
#define ROBLOX_BATCHED_SURFACE_INCLUDED

// Roblox batched surface: vertex-color and per-vertex surface data.
//   flags bit0 _IS_TEXTURE, bit1 _IS_LEGODETAIL, bit2 _IS_CHECKERDETAIL, bit3 _IS_ALBEDO_MOVEMENT, bit4 _EMISSION
TEXTURE2D(_Albedo1); SAMPLER(sampler_Albedo1);
TEXTURE2D(_Albedo2); SAMPLER(sampler_Albedo2);
TEXTURE2D(_Albedo3); SAMPLER(sampler_Albedo3);
TEXTURE2D(_Albedo4); SAMPLER(sampler_Albedo4);
TEXTURE2D(_LegoDetail); SAMPLER(sampler_LegoDetail);
TEXTURE2D(_LegoNormal); SAMPLER(sampler_LegoNormal);
TEXTURE2D(_CheckerDetail); SAMPLER(sampler_CheckerDetail);

half4 RobloxAlbedo(float2 uv, int slot)
{
    half4 c = half4(1, 1, 1, 1);
    if (slot == 1) c = SAMPLE_TEXTURE2D(_Albedo1, sampler_Albedo1, uv);
    else if (slot == 2) c = SAMPLE_TEXTURE2D(_Albedo2, sampler_Albedo2, uv);
    else if (slot == 3) c = SAMPLE_TEXTURE2D(_Albedo3, sampler_Albedo3, uv);
    else if (slot == 4) c = SAMPLE_TEXTURE2D(_Albedo4, sampler_Albedo4, uv);
    return c;
}

void RobloxSurfaceFromData(float2 uvL, half4 base, float4 pb1, float2 pb2, out SurfaceData surfaceData)
{
    surfaceData = (SurfaceData)0;
    int flags = (int)(pb1.x + 0.5);
    int slot = (int)(pb1.y + 0.5);
    bool isTexture = (flags & 1) != 0;
    bool isLego = (flags & 2) != 0;
    bool isChecker = (flags & 4) != 0;
    bool isMove = (flags & 8) != 0;
    bool isEmission = (flags & 16) != 0;

    half4 colorOut = base;
    half3 normalTS = half3(0, 0, 1);
    if (isTexture)
    {
        float2 albedoUV = isMove ? uvL - _TimeParameters.x * pb2 : uvL;
        half4 albedo = RobloxAlbedo(albedoUV, slot);
        half4 checkerTerm = base;
        if (isChecker)
            checkerTerm = base * SAMPLE_TEXTURE2D(_CheckerDetail, sampler_CheckerDetail, uvL / round(pb1.z));
        half4 legoTerm = base;
        if (isLego)
        {
            legoTerm = SAMPLE_TEXTURE2D(_LegoDetail, sampler_LegoDetail, uvL);
            normalTS = UnpackNormal(SAMPLE_TEXTURE2D(_LegoNormal, sampler_LegoNormal, uvL));
        }
        colorOut = albedo * (checkerTerm * legoTerm);
    }

    surfaceData.albedo = colorOut.rgb;
    surfaceData.alpha = base.a;
    surfaceData.metallic = 0;
    surfaceData.specular = half3(0.5, 0.5, 0.5);
    surfaceData.smoothness = 0;
    surfaceData.occlusion = 1;
    surfaceData.normalTS = normalTS;
    surfaceData.emission = isEmission ? (colorOut * base * pb1.w).rgb : half3(0, 0, 0);
}

#endif
