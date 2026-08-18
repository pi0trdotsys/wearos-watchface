package dev.rosinski.watchface.energybridge;

import android.content.Context;

/** Stores only the latest numeric score received from the paired phone. */
final class EnergyScoreStore {
    private static final String FILE = "energy_score";
    private static final String VALUE = "value";

    private EnergyScoreStore() {}

    static void save(Context context, int score) {
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
                .edit()
                .putInt(VALUE, score)
                .apply();
    }

    static int read(Context context) {
        return context.getSharedPreferences(FILE, Context.MODE_PRIVATE).getInt(VALUE, -1);
    }
}
