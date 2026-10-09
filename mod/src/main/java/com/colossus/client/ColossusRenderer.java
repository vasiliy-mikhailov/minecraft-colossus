package com.colossus.client;

import com.colossus.ColossusEntity;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;

/** Colossus renderer: full-size 52-px model (ground at model y=24, so no scale/translate), plus glowing eye slits. */
public class ColossusRenderer extends MobRenderer<ColossusEntity, ColossusModel> {
    public static final ResourceLocation TEXTURE = ColossusModel.TEXTURE;

    public ColossusRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new ColossusModel(ctx.bakeLayer(ColossusModel.LAYER)), 1.0F);
        this.addLayer(new ColossusEyesLayer(this));
    }

    @Override
    public ResourceLocation getTextureLocation(ColossusEntity entity) {
        return TEXTURE;
    }
}
