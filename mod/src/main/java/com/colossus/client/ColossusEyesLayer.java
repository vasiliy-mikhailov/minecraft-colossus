package com.colossus.client;

import com.colossus.ColossusEntity;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.EyesLayer;

/** Full-bright glowing eye slits: renders colossus_eyes.png (only the eye texels are opaque) with RenderType.eyes. */
public class ColossusEyesLayer extends EyesLayer<ColossusEntity, ColossusModel> {
    private static final RenderType EYES = RenderType.eyes(ColossusModel.EYES_TEXTURE);

    public ColossusEyesLayer(RenderLayerParent<ColossusEntity, ColossusModel> parent) {
        super(parent);
    }

    @Override
    public RenderType renderType() {
        return EYES;
    }
}
