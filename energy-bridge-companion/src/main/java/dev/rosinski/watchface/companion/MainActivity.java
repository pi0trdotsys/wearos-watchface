package dev.rosinski.watchface.companion;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.wearable.PutDataMapRequest;
import com.google.android.gms.wearable.PutDataRequest;
import com.google.android.gms.wearable.Wearable;

public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(64, 64, 64, 64);

        TextView statusText = new TextView(this);
        statusText.setText("Nine Eleven Energy Companion\nGotowy do synchronizacji.");
        statusText.setTextSize(18f);

        Button syncButton = new Button(this);
        syncButton.setText("Pobierz Energy Score i Wyślij na Zegarek");
        syncButton.setOnClickListener(v -> syncEnergyScore(statusText));

        layout.addView(statusText);
        layout.addView(syncButton);
        setContentView(layout);
    }

    private void syncEnergyScore(TextView statusTextView) {
        int energyScore = fetchEnergyScoreFromSamsungHealth();

        PutDataMapRequest putDataMapReq = PutDataMapRequest.create("/energy_score");
        putDataMapReq.getDataMap().putInt("score", energyScore);
        putDataMapReq.getDataMap().putLong("timestamp", System.currentTimeMillis());

        PutDataRequest request = putDataMapReq.asPutDataRequest();
        request.setUrgent();

        Wearable.getDataClient(this).putDataItem(request)
            .addOnSuccessListener(dataItem -> {
                statusTextView.setText("Pomyślnie wysłano Energy Score: " + energyScore + " do zegarka!");
                Toast.makeText(MainActivity.this, "Wysłano: " + energyScore, Toast.LENGTH_SHORT).show();
            })
            .addOnFailureListener(e -> {
                statusTextView.setText("Błąd synchronizacji: " + e.getLocalizedMessage());
            });
    }

    private int fetchEnergyScoreFromSamsungHealth() {
        return 85;
    }
}
