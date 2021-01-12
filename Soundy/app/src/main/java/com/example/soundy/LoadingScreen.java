package com.example.soundy;


import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ObjectAnimator;
import android.animation.PropertyValuesHolder;
import android.content.Intent;
import android.content.res.Resources;
import android.graphics.Color;
import android.graphics.Path;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.TypedValue;
import android.view.View;
import android.view.ViewAnimationUtils;
import android.view.Window;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import android.content.res.Resources;
import android.os.Bundle;
import android.widget.ImageView;

import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;


public class LoadingScreen extends AppCompatActivity {
    ImageView filled;
    ImageView circle;
    ImageView[] orb;
    ImageView circle1;
    String[] isSpeaking = new String[4];
    String[] content = new String[4];
    String[] classification = new String[4];
    TextView[] text ;


    @RequiresApi(api = Build.VERSION_CODES.LOLLIPOP)
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        getWindow().setStatusBarColor(Color.parseColor("#06d6a0"));
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_loading_screen);
        getSupportActionBar().hide();



        filled = findViewById(R.id.filled);
        circle = findViewById(R.id.circle);
        circle1 = findViewById(R.id.circle1);


        orb = new ImageView[4];
        orb[0] = findViewById(R.id.orb1);
        orb[1] = findViewById(R.id.orb2);
        orb[2] = findViewById(R.id.orb3);
        orb[3] = findViewById(R.id.orb4);

        text = new TextView[4];
        text[0]=findViewById(R.id.text1);
        text[1]=findViewById(R.id.text2);
        text[2]=findViewById(R.id.text3);
        text[3]=findViewById(R.id.text4);



        ObjectAnimator scaleDown = ObjectAnimator.ofPropertyValuesHolder(
                filled,
                PropertyValuesHolder.ofFloat("scaleX", 1.2f),
                PropertyValuesHolder.ofFloat("scaleY", 1.2f));
        scaleDown.setDuration(1500);

        scaleDown.setRepeatCount(ObjectAnimator.INFINITE);
        scaleDown.setRepeatMode(ObjectAnimator.REVERSE);

        scaleDown.start();

        int orbRadius = (int) (w()*.05);

        for (int i=0;i<4;i++)
            orb[i].setVisibility(View.GONE);

        final float centerX= (float) (w()/2.0);
        final float centerY = (float) (h()*0.3);
        int filledRadius = (int) (w()*0.55);
        final int circleRadius = (int) (w()*0.8);
        int circleRadius1 =  (int) (w()*0.84);
        float[] temp = centerToTopLeft(centerX,centerY,filledRadius);
        initialize(filled, temp[0], temp[1],filledRadius);
        temp = centerToTopLeft(centerX,centerY,circleRadius);
        initialize(circle,temp[0],temp[1],circleRadius);
        temp = centerToTopLeft(centerX,centerY,circleRadius1);
        initialize(circle1,temp[0],temp[1],circleRadius1);



        final FirebaseDatabase database = FirebaseDatabase.getInstance();

        final DatabaseReference sound = database.getReference("Sound");
        sound.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                int count=0;
                for (DataSnapshot snapshot: dataSnapshot.getChildren())
                {

                    isSpeaking[count]=  snapshot.child("speaking").getValue().toString();
                    content[count] = snapshot.child("content").getValue().toString();
                    classification[count] = snapshot.child("classification").getValue().toString();
                    if (isSpeaking[count].equals("true")) {
                        text[count].setTextSize(TypedValue.COMPLEX_UNIT_DIP,10);
                        text[count].setText(content[count]);
                    }

                    count++;
                }
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });
        DatabaseReference xyval = database.getReference("x_and_y");
        final float[] finalTemp = temp;
        xyval.addValueEventListener(new ValueEventListener() {
            @RequiresApi(api = Build.VERSION_CODES.KITKAT)
            @Override
            public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                int count = 0;
                for (DataSnapshot snapshot : dataSnapshot.getChildren()) {
                    String visibility = snapshot.child("visibility").getValue().toString();
                    if (visibility.equals("true"))
                    {
                        if (isSpeaking[count].equals("false")) {
                            text[count].setTextSize(TypedValue.COMPLEX_UNIT_DIP,10);
                            String[] split = classification[count].split(" ");
                            String[] temp=split;
                            System.out.println(temp.toString());
                            if (split.length>12)
                            {

                                temp = subArray(split,12,split.length);
                            }
                            classification[count]= temp.toString().replace("[","").replace("]","").replace(",","");
                            text[count].setText(classification[count]);
                        }
                        String[] val = snapshot.child("cords").getValue().toString().split(" ");
                        //orb[count].setColorFilter(Color.parseColor(colors[count]));
                        float sampleX = Float.parseFloat(val[0]);
                        float sampleY = Float.parseFloat(val[1]);
                        float constantX=1;
                        float constantY=1;
                        //top right
                        if (sampleX>0 && sampleY>0)
                        {
                            constantX=1;
                            constantY=-1;
                        }
                        //top left
                        else if (sampleX<0 && sampleY>0)
                        {
                            constantX=-1;
                            constantY=1;
                        }
                        //
                        else if (sampleX<0 && sampleY<0)
                        {
                            constantX=-1;
                            constantY=1;
                        }
                        else if (sampleX>0 && sampleY<0)
                        {
                            constantX=1;
                            constantY=-1;
                        }

                        float deg = (float) Math.atan(sampleY/sampleX);
                        sampleX = (float) (Math.cos(deg)*circleRadius/2.0*constantX +centerX);
                        sampleY = (float) (Math.sin(deg)*circleRadius/2.0*constantY +centerY);

                        int orbRadius = (int) (w()*.09);
                        float[] temp = centerToTopLeft(sampleX,sampleY,orbRadius);
                        initialize(orb[count],temp[0],temp[1],orbRadius);
                        orb[count].setVisibility(View.VISIBLE);


                    }
                    else
                    {
                        orb[count].setVisibility(View.GONE);
                    }
                    count++;
                }
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {
            }
        });


    }
    public static float[] centerToTopLeft(float x, float y, int radius)
    {
        float newY = (float) (y-radius/2.0);
        float newX = (float) (x-radius/2.0);
        return new float[]{newX, newY};
    }
    public static int w() {
        return Resources.getSystem().getDisplayMetrics().widthPixels;
    }

    public static int h() {
        return Resources.getSystem().getDisplayMetrics().heightPixels;
    }
    public static void initialize(ImageView view, float x, float y, int radius)
    {
        view.setX(x);
        view.setY(y);
        view.getLayoutParams().height = radius;
        view.getLayoutParams().width = radius;
    }
    public static<T> T[] subArray(T[] array, int beg, int end) {
        return Arrays.copyOfRange(array, beg, end + 1);
    }
}