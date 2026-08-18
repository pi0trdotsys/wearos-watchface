package dev.rosinski.watchface.companion;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.wearable.PutDataMapRequest;
import com.google.android.gms.wearable.PutDataRequest;
import com.google.android.gms.wearable.Wearable;

public class MainActivity extends Activity {

    private static final String TAG = "EnergyBridgeCompanion";

    /** Must match EnergyScoreDataListenerService.PATH on the watch side,
     * or the intent-filter's pathPrefix never matches and nothing arrives. */
    private static final String PATH = "/nine-eleven/energy-score";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Explicit colors throughout: Theme.DeviceDefault's inherited text
        // color resolved to black-on-near-black on this device (MIUI), which
        // made the whole screen below the title look blank - button included
        // - so every earlier tap landed on nothing. Never rely on inherited
        // theme defaults for a screen this bare; state every color.
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(64, 64, 64, 64);
        layout.setBackgroundColor(Color.parseColor("#1a1f1a"));

        TextView statusText = new TextView(this);
        statusText.setText("Nine Eleven Energy Companion\nGotowy do synchronizacji.");
        statusText.setTextSize(18f);
        statusText.setTextColor(Color.WHITE);
        statusText.setPadding(0, 0, 0, 48);

        Button syncButton = new Button(this);
        syncButton.setText("Pobierz Energy Score i wyślij na zegarek");
        syncButton.setTextColor(Color.WHITE);
        syncButton.setBackgroundColor(Color.parseColor("#fb6d27"));
        syncButton.setOnClickListener(v -> syncEnergyScore(statusText));

        layout.addView(statusText);
        layout.addView(syncButton);
        setContentView(layout);
    }

    private void syncEnergyScore(TextView statusTextView) {
        int energyScore = fetchEnergyScoreFromSamsungHealth();
        Log.d(TAG, "Sending score=" + energyScore + " to path=" + PATH);

        PutDataMapRequest putDataMapReq = PutDataMapRequest.create(PATH);
        putDataMapReq.getDataMap().putInt("score", energyScore);
        putDataMapReq.getDataMap().putLong("timestamp", System.currentTimeMillis());

        PutDataRequest request = putDataMapReq.asPutDataRequest();
        request.setUrgent();

        Wearable.getDataClient(this).putDataItem(request)
            .addOnSuccessListener(dataItem -> {
                Log.d(TAG, "putDataItem succeeded: " + dataItem.getUri());
                statusTextView.setText("Pomyślnie wysłano Energy Score: " + energyScore + " do zegarka!");
                Toast.makeText(MainActivity.this, "Wysłano: " + energyScore, Toast.LENGTH_SHORT).show();
            })
            .addOnFailureListener(e -> {
                Log.e(TAG, "putDataItem failed", e);
                statusTextView.setText("Błąd synchronizacji: " + e.getLocalizedMessage());
            });
    }

    /**
     * TODO(real data): this is a stub - it does not read Samsung Health.
     * Reading Energy Score for real needs the Samsung Health Data SDK
     * (separate partner license from Samsung) or Health Connect once/if it
     * exposes an equivalent record type, plus the runtime permission grant
     * dance on the phone. Until that's wired up, every sync sends this
     * fixed number, which is fine for exercising the watch-side plumbing
     * but must not be mistaken for a working integration.
     */
    private int fetchEnergyScoreFromSamsungHealth() {
        return 85;
    }
}
