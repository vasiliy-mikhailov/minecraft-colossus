package com.colossus;

import java.util.EnumSet;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/** Colossus: a non-hostile PathfinderMob (exists on peaceful) that walks up to the nearest player. */
public class ColossusEntity extends PathfinderMob {

    public ColossusEntity(EntityType<? extends ColossusEntity> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 100.0)
                .add(Attributes.MOVEMENT_SPEED, 0.23)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new ApproachPlayerGoal(this, 1.0, 32.0, 3.0));
        this.goalSelector.addGoal(2, new LookAtPlayerGoal(this, Player.class, 16.0F));
        this.goalSelector.addGoal(3, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(4, new RandomLookAroundGoal(this));
    }

    @Override
    public boolean removeWhenFarAway(double distanceToClosestPlayer) {
        return false; // a summoned colossus stays put
    }

    /** Entity tag that, when present on a nearby living entity (e.g. an invisible armor stand), overrides the player as
     *  the walk target. Used to film the walk from the side/back; without such an entity behaviour is unchanged. */
    public static final String LURE_TAG = "colossus_lure";

    /** Walk toward the nearest lure-tagged entity, else the nearest (non-spectator) player, within {@code range},
     *  stopping at {@code stopDist}. */
    static class ApproachPlayerGoal extends Goal {
        private final PathfinderMob mob;
        private final double speed;
        private final double range;
        private final double stopDist;
        private LivingEntity target;
        private int repathIn;

        ApproachPlayerGoal(PathfinderMob mob, double speed, double range, double stopDist) {
            this.mob = mob;
            this.speed = speed;
            this.range = range;
            this.stopDist = stopDist;
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity p = mob.level().getEntitiesOfClass(LivingEntity.class,
                            mob.getBoundingBox().inflate(range), e -> e.getTags().contains(LURE_TAG))
                    .stream().min(java.util.Comparator.comparingDouble(mob::distanceToSqr)).orElse(null);
            if (p == null) p = mob.level().getNearestPlayer(mob, range);
            if (p == null || mob.distanceToSqr(p) <= stopDist * stopDist) return false;
            target = p;
            return true;
        }

        @Override
        public boolean canContinueToUse() {
            return target != null && target.isAlive() && !target.isSpectator()
                    && mob.distanceToSqr(target) > stopDist * stopDist
                    && mob.distanceToSqr(target) <= range * range;
        }

        @Override
        public void start() {
            repathIn = 0;
        }

        @Override
        public void stop() {
            target = null;
            mob.getNavigation().stop();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            mob.getLookControl().setLookAt(target, 30.0F, 30.0F);
            if (--repathIn <= 0) {
                repathIn = 10;
                mob.getNavigation().moveTo(target, speed);
            }
        }
    }
}
